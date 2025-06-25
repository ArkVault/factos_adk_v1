from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from adk_project.agents.fact_check_matcher_agent.prompt import MATCHER_PROMPT
from adk_project.agents.fact_check_matcher_agent.factchecker_scraper import get_factchecker_claims
import os
import aiohttp
import asyncio

async def gemini_complete(prompt: str, model: str = "gemini-2.5-flash") -> str:
    """
    Wrapper eficiente para llamar a Gemini 2.5 vía API REST de Google Generative Language.
    Requiere la variable de entorno GOOGLE_API_KEY.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Falta GOOGLE_API_KEY en el entorno para usar Gemini.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data, timeout=30) as resp:
            if resp.status == 200:
                result = await resp.json()
                return result["candidates"][0]["content"]["parts"][0]["text"]
            else:
                raise RuntimeError(f"Error en Gemini API: {resp.status}")

async def semantic_match_with_gemini(claim, factchecker_claims):
    """
    Usa Gemini 2.5 para hacer matching semántico inteligente y flexible entre claims.
    Evalúa equivalencias, contradicciones y relaciones semánticas, no solo matches exactos.
    """
    if not factchecker_claims:
        return {"semantic_matches": [], "explanation": "No hay claims de fact-checkers disponibles para comparar."}
    
    # Preparar claims para análisis más detallado
    claims_text = ""
    for i, fc in enumerate(factchecker_claims):
        texto = fc.get('main_claim') or fc.get('headline') or fc.get('title', '')
        source = fc.get('source', 'Desconocida')
        verdict = fc.get('rating') or fc.get('verdict', 'No especificado')
        claims_text += f"{i+1}. [{source}] {texto} (Veredicto: {verdict})\n"
    
    prompt = f"""
    Como experto en análisis semántico y verificación de hechos, evalúa la relación entre un claim original y verificaciones existentes.

    IMPORTANTE: Busca relaciones semánticas FLEXIBLES, no solo matches exactos. Considera:
    - Mismos hechos expresados de forma diferente
    - Afirmaciones que contradicen o apoyan el claim principal
    - Claims sobre el mismo evento/tema aunque con enfoques distintos
    - Información relacionada que puede ser relevante para la verificación

    CLAIM A VERIFICAR:
    "{claim}"

    VERIFICACIONES DISPONIBLES:
    {claims_text}

    Para cada verificación relevante, evalúa:
    1. TIPO DE RELACIÓN: equivalente, contradictorio, relacionado, tangencial, sin_relacion
    2. NIVEL DE CONFIANZA: alto (85%+), medio (60-84%), bajo (30-59%)
    3. EXPLICACIÓN: Por qué es relevante y cómo se relaciona semánticamente

    Responde SOLO en formato JSON válido:
    {{
        "semantic_matches": [
            {{
                "index": int,
                "source": "string", 
                "relation_type": "equivalente|contradictorio|relacionado|tangencial",
                "confidence_level": "alto|medio|bajo",
                "explanation": "explicación detallada de la relación semántica",
                "original_text": "texto original del fact-checker"
            }}
        ],
        "overall_analysis": "análisis general del conjunto de verificaciones disponibles"
    }}

    CRITERIOS DE INCLUSIÓN:
    - Equivalente: Mismo hecho, diferentes palabras (confianza: alto)
    - Contradictorio: Niega directamente el claim (confianza: alto)
    - Relacionado: Sobre el mismo evento/tema (confianza: medio/alto)
    - Tangencial: Contexto relacionado pero no directamente (confianza: bajo/medio)

    Incluye AL MENOS las verificaciones con confianza media o alta, incluso si no son matches exactos.
    """
    
    try:
        response = await gemini_complete(prompt)
        import json
        result = json.loads(response.strip())
        
        # Enriquecer los matches con datos originales
        enriched_matches = []
        for match in result.get('semantic_matches', []):
            if 0 <= match['index'] < len(factchecker_claims):
                original_fc = factchecker_claims[match['index']]
                enriched_match = {
                    **match,
                    'url': original_fc.get('url', ''),
                    'rating': original_fc.get('rating') or original_fc.get('verdict', ''),
                    'publish_date': original_fc.get('publish_date', ''),
                    'main_claim': original_fc.get('main_claim') or original_fc.get('headline', ''),
                }
                enriched_matches.append(enriched_match)
        
        return {
            "semantic_matches": enriched_matches,
            "explanation": result.get('overall_analysis', 'Análisis semántico completado'),
            "total_evaluated": len(factchecker_claims),
            "relevant_found": len(enriched_matches)
        }
        
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parseando respuesta de Gemini: {e}")
        # Fallback: matching simple por palabras clave
        return await simple_keyword_matching(claim, factchecker_claims)
    except Exception as e:
        print(f"Error en análisis semántico: {e}")
        return {"semantic_matches": [], "explanation": f"Error en análisis semántico: {str(e)}"}

async def simple_keyword_matching(claim, factchecker_claims):
    """Fallback: matching simple basado en palabras clave cuando Gemini falla"""
    import re
    
    claim_words = set(re.findall(r'\b\w+\b', claim.lower()))
    matches = []
    
    for i, fc in enumerate(factchecker_claims):
        fc_text = (fc.get('main_claim', '') + ' ' + fc.get('headline', '')).lower()
        fc_words = set(re.findall(r'\b\w+\b', fc_text))
        
        # Calcular similitud por intersección de palabras
        intersection = claim_words.intersection(fc_words)
        similarity = len(intersection) / max(len(claim_words), len(fc_words)) if claim_words or fc_words else 0
        
        if similarity > 0.3:  # 30% similitud mínima
            confidence = "alto" if similarity > 0.6 else "medio" if similarity > 0.4 else "bajo"
            matches.append({
                "index": i,
                "source": fc.get('source', 'Desconocida'),
                "relation_type": "relacionado",
                "confidence_level": confidence,
                "explanation": f"Similitud de palabras clave: {similarity:.1%} ({len(intersection)} palabras comunes)",
                "original_text": fc.get('main_claim') or fc.get('headline', ''),
                "url": fc.get('url', ''),
                "rating": fc.get('rating') or fc.get('verdict', '')
            })
    
    return {
        "semantic_matches": matches,
        "explanation": f"Análisis por palabras clave (fallback). Evaluados: {len(factchecker_claims)}, relevantes: {len(matches)}",
        "total_evaluated": len(factchecker_claims),
        "relevant_found": len(matches)
    }

async def factchecker_search_tool(main_claim: str):
    """
    Herramienta mejorada que combina búsqueda tradicional con análisis semántico inteligente.
    Busca matches exactos primero, luego usa Gemini para matching flexible.
    """
    # Paso 1: Búsqueda tradicional
    claims = await get_factchecker_claims(main_claim)
    
    # Paso 2: Evaluar calidad de matches tradicionales
    high_score_matches = [c for c in claims if c.get('score', 0) >= 85]
    medium_score_matches = [c for c in claims if 60 <= c.get('score', 0) < 85]
    
    # Paso 3: Análisis semántico para mejorar matching
    semantic_result = await semantic_match_with_gemini(main_claim, claims)
    semantic_matches = semantic_result.get('semantic_matches', [])
    
    # Paso 4: Combinar resultados inteligentemente
    combined_matches = []
    
    # Añadir matches de alta confianza (exactos o semánticamente equivalentes)
    for match in high_score_matches:
        combined_matches.append({
            **match,
            'match_type': 'traditional_high',
            'confidence': 'alto'
        })
    
    # Añadir matches semánticamente relevantes con alta confianza
    for sem_match in semantic_matches:
        if sem_match.get('confidence_level') == 'alto':
            # Buscar el claim original correspondiente
            original_claim = None
            if 0 <= sem_match['index'] < len(claims):
                original_claim = claims[sem_match['index']]
            
            if original_claim and not any(m.get('url') == original_claim.get('url') for m in combined_matches):
                combined_matches.append({
                    **original_claim,
                    'match_type': 'semantic_high',
                    'confidence': 'alto',
                    'relation_type': sem_match.get('relation_type'),
                    'semantic_explanation': sem_match.get('explanation')
                })
    
    # Añadir matches de confianza media si no hay suficientes de alta confianza
    if len(combined_matches) < 3:
        for match in medium_score_matches:
            if not any(m.get('url') == match.get('url') for m in combined_matches):
                combined_matches.append({
                    **match,
                    'match_type': 'traditional_medium',
                    'confidence': 'medio'
                })
        
        # Añadir matches semánticos de confianza media
        for sem_match in semantic_matches:
            if sem_match.get('confidence_level') == 'medio' and len(combined_matches) < 5:
                original_claim = None
                if 0 <= sem_match['index'] < len(claims):
                    original_claim = claims[sem_match['index']]
                
                if original_claim and not any(m.get('url') == original_claim.get('url') for m in combined_matches):
                    combined_matches.append({
                        **original_claim,
                        'match_type': 'semantic_medium',
                        'confidence': 'medio',
                        'relation_type': sem_match.get('relation_type'),
                        'semantic_explanation': sem_match.get('explanation')
                    })
    
    # Paso 5: Preparar resultado final
    result = {
        "matches": combined_matches[:5],  # Máximo 5 matches más relevantes
        "total_found": len(claims),
        "semantic_analysis": {
            "explanation": semantic_result.get('explanation', ''),
            "total_evaluated": semantic_result.get('total_evaluated', 0),
            "relevant_found": semantic_result.get('relevant_found', 0)
        },
        "search_summary": f"Búsqueda tradicional: {len(claims)} resultados. Análisis semántico: {len(semantic_matches)} matches relevantes. Combinados: {len(combined_matches)} matches finales."
    }
    
    return result

factchecker_tool = FunctionTool(factchecker_search_tool)

class FactCheckMatcherAgent(LlmAgent):
    def __init__(self):
        super().__init__(
            name="FactCheckMatcherAgent",
            instruction=MATCHER_PROMPT + "\n\nUtiliza la herramienta factchecker_tool para buscar claims relevantes en tiempo real.",
            description="Busca la afirmación en la base local de fact-checks y en tiempo real en los principales fact-checkers.",
            output_key="match_results",
            tools=[factchecker_tool],
            model="gemini-2.5-flash"
        )

    async def run_async(self, ctx):
        claim = ctx.session.state.get("extracted_claim", {}).get("claim", "")
        if not claim:
            ctx.session.state["match_results"] = {"matches": []}
            yield
            return
        
        print(f"[FactCheckMatcherAgent] 🚀 SMART SEARCH for claim: {claim[:100]}...")
        
        # STRATEGY 1: Perplexity Sonar with fact-checker domain filters
        print("[FactCheckMatcherAgent] 🥇 Step 1: Perplexity domain-filtered search...")
        perplexity_matches = await self._search_with_perplexity_enhanced(claim)
        
        # Analyze quality of matches
        strong_matches = self._analyze_match_quality(perplexity_matches, claim)
        
        if strong_matches["has_strong_matches"]:
            print(f"[FactCheckMatcherAgent] ✅ Found {len(strong_matches['strong'])} STRONG matches - analysis will be conclusive")
            ctx.session.state["match_results"] = {
                "matches": perplexity_matches,
                "search_method": "perplexity_primary",
                "match_quality": "strong",
                "confidence_level": "high",
                "total_found": len(perplexity_matches)
            }
            yield
            return
        
        elif strong_matches["has_moderate_matches"]:
            print(f"[FactCheckMatcherAgent] ⚠️ Found {len(strong_matches['moderate'])} moderate matches - expanding search...")
            
            # STRATEGY 2: Expand to additional verificators
            print("[FactCheckMatcherAgent] 🔍 Step 2: Expanding to additional verificators...")
            additional_matches = await self._search_additional_verificators(claim)
            
            all_matches = perplexity_matches + additional_matches
            combined_quality = self._analyze_match_quality(all_matches, claim)
            
            if combined_quality["has_strong_matches"]:
                print(f"[FactCheckMatcherAgent] ✅ Expansion successful - found strong matches")
                ctx.session.state["match_results"] = {
                    "matches": all_matches,
                    "search_method": "perplexity + expanded_verificators",
                    "match_quality": "strong",
                    "confidence_level": "high",
                    "total_found": len(all_matches)
                }
            else:
                print(f"[FactCheckMatcherAgent] ⚠️ Moderate matches only - analysis will be cautious")
                ctx.session.state["match_results"] = {
                    "matches": all_matches,
                    "search_method": "perplexity + expanded_verificators",
                    "match_quality": "moderate",
                    "confidence_level": "medium",
                    "total_found": len(all_matches)
                }
            yield
            return
        
        # STRATEGY 3: No good matches in fact-checkers, search verified media sources
        print("[FactCheckMatcherAgent] � Step 3: Searching verified media sources...")
        
        # Search verified media sources for coverage of the claim
        verified_media_matches = await self._search_verified_media_sources(claim)
        
        # Try Firecrawl for broader news verification (fast)
        firecrawl_matches = await self._search_with_firecrawl_enhanced(claim)
        
        # Combine all sources
        all_alternative_matches = verified_media_matches + firecrawl_matches
        
        # SKIP traditional webcrawling completely if we have ANY results
        total_existing_matches = len(perplexity_matches) + len(all_alternative_matches)
        
        if total_existing_matches == 0:
            print("[FactCheckMatcherAgent] ⚠️ NO results from smart search - attempting MINIMAL ultra-fast crawl...")
            # Only crawl as absolute last resort with ultra-strict timeout
            traditional_matches = await self._quick_factcheck_crawl(claim)
        else:
            print(f"[FactCheckMatcherAgent] ✅ SKIPPING crawling - found {total_existing_matches} matches from smart search")
            traditional_matches = []
        
        all_matches = perplexity_matches + all_alternative_matches + traditional_matches
        
        # Determinar calidad basada en tipos de fuentes encontradas
        if verified_media_matches:
            match_quality = "moderate"  # Medios verificados dan confianza moderada
            confidence_level = "medium"
            search_method = "efficient_search + verified_media"
        else:
            match_quality = "weak"
            confidence_level = "low"
            search_method = "efficient_search"
        
        print(f"[FactCheckMatcherAgent] ⚠️ Analysis will be {confidence_level.upper()} confidence - total matches: {len(all_matches)}")
        ctx.session.state["match_results"] = {
            "matches": all_matches[:8],  # Incluir más matches cuando hay medios verificados
            "search_method": search_method,
            "match_quality": match_quality,
            "confidence_level": confidence_level,
            "total_found": len(all_matches),
            "verified_media_found": len(verified_media_matches),
            "factcheck_found": len(perplexity_matches)
        }
        
        yield
    
    async def _quick_factcheck_crawl(self, claim: str) -> list:
        """Quick crawl of only the fastest fact-checkers with aggressive timeout"""
        try:
            print(f"[FactCheckMatcherAgent] 🚀 Starting ULTRA-QUICK crawl (max 10 seconds)...")
            
            # Import the function with aggressive timeout
            import asyncio
            
            # Set an extremely strict timeout for the quick crawl
            try:
                # Use an even shorter timeout - 10 seconds max
                matches = await asyncio.wait_for(
                    get_factchecker_claims(claim), 
                    timeout=10.0  # Max 10 seconds for quick crawl
                )
                result = matches if isinstance(matches, list) else []
                print(f"[FactCheckMatcherAgent] ✅ Ultra-quick crawl completed: {len(result)} matches in <10s")
                return result
            except asyncio.TimeoutError:
                print("[FactCheckMatcherAgent] ⏰ Ultra-quick crawl timed out after 10s - SKIPPING completamente")
                return []
                
        except Exception as e:
            print(f"[FactCheckMatcherAgent] Error in ultra-quick crawl: {e}")
            return []
    
    def _analyze_match_quality(self, matches: list, original_claim: str) -> dict:
        """Analyze the quality and relevance of fact-check matches"""
        if not matches:
            return {"has_strong_matches": False, "has_moderate_matches": False, "strong": [], "moderate": [], "weak": []}
        
        strong_matches = []
        moderate_matches = []
        weak_matches = []
        
        for match in matches:
            similarity_score = self._calculate_semantic_similarity(original_claim, match.get('main_claim', ''))
            
            # Check if it's from a major fact-checker
            is_major_factchecker = any(source in match.get('source', '').lower() 
                                     for source in ['snopes', 'politifact', 'factcheck.org', 'reuters', 'ap'])
            
            # Check if it has a clear verdict
            has_clear_verdict = match.get('rating', '').lower() in ['true', 'false', 'mostly true', 'mostly false', 'misleading']
            
            # Categorize match quality
            if similarity_score > 0.7 and is_major_factchecker and has_clear_verdict:
                strong_matches.append(match)
            elif similarity_score > 0.4 and (is_major_factchecker or has_clear_verdict):
                moderate_matches.append(match)
            else:
                weak_matches.append(match)
        
        return {
            "has_strong_matches": len(strong_matches) > 0,
            "has_moderate_matches": len(moderate_matches) > 0,
            "strong": strong_matches,
            "moderate": moderate_matches,
            "weak": weak_matches,
            "total_strong": len(strong_matches),
            "total_moderate": len(moderate_matches)
        }
    
    def _calculate_semantic_similarity(self, claim1: str, claim2: str) -> float:
        """Calculate semantic similarity between two claims"""
        if not claim1 or not claim2:
            return 0.0
        
        # Simple word-based similarity for now
        words1 = set(claim1.lower().split())
        words2 = set(claim2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def _search_additional_verificators(self, claim: str) -> list:
        """Search additional verificators when main fact-checkers don't have matches"""
        try:
            import aiohttp
            
            api_key = os.environ.get("PERPLEXITY_API_KEY")
            if not api_key:
                return []
            
            # Extended list of verificators for broader search
            additional_domains = [
                "bbc.com/news/reality-check",
                "cnn.com/factsfirst",
                "washingtonpost.com/news/fact-checker",
                "theguardian.com/world/reality-check",
                "factcheckni.org",
                "africacheck.org",
                "checkyourfact.com",
                "leadstories.com",
                "truthorfiction.com"
            ]
            
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""
            Search for verification, fact-checks, or debunking articles about this claim: "{claim}"
            
            Look beyond major fact-checkers for:
            1. News organizations' fact-check sections
            2. Regional fact-checkers and verification outlets
            3. Academic or institutional verification
            4. Journalistic investigations that verify or debunk similar claims
            
            Focus on finding actual verification work, not just news reporting.
            """
            
            data = {
                "model": "llama-3.1-sonar-large-128k-online",
                "messages": [{"role": "user", "content": prompt}],
                "search_domain_filter": additional_domains,
                "max_tokens": 400,
                "temperature": 0.1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=30) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        content = result["choices"][0]["message"]["content"]
                        
                        print(f"[FactCheckMatcherAgent] 🔍 Additional verificators search: {len(content)} chars")
                        return self._parse_additional_verificators_response(content)
                    else:
                        print(f"[FactCheckMatcherAgent] Additional search API error: {resp.status}")
                        return []
                        
        except Exception as e:
            print(f"[FactCheckMatcherAgent] Error in additional verificators search: {e}")
            return []
    
    def _parse_additional_verificators_response(self, content: str) -> list:
        """Parse response from additional verificators search"""
        matches = []
        
        if not content or len(content) < 50:
            return matches
        
        # Look for verification indicators
        verification_indicators = ['verified', 'debunked', 'investigated', 'fact-check', 'reality check', 'analysis']
        
        if any(indicator in content.lower() for indicator in verification_indicators):
            matches.append({
                'source': 'Additional Verificators',
                'url': '',
                'title': 'Extended Verification Search',
                'main_claim': content[:350] + '...' if len(content) > 350 else content,
                'rating': self._extract_overall_verdict(content),
                'confidence': 'medio',
                'match_type': 'additional_verificators',
                'publish_date': '',
                'relation_to_claim': 'verification'
            })
        
        return matches
    
    async def _search_with_firecrawl_enhanced(self, claim: str) -> list:
        """Enhanced Firecrawl search targeting specific fact-check sites"""
        try:
            api_key = os.environ.get("FIRECRAWL_API_KEY")
            if not api_key:
                print("[FactCheckMatcherAgent] No Firecrawl API key found")
                return []
            
            # Focused fact-check sites for more targeted search
            factcheck_sites = [
                "site:snopes.com",
                "site:politifact.com", 
                "site:factcheck.org",
                "site:reuters.com/fact-check",
                "site:apnews.com/hub/ap-fact-check",
                "site:fullfact.org",
                "site:checkyourfact.com"
            ]
            
            all_matches = []
            
            # Extract key terms from claim for better search
            key_terms = self._extract_key_terms(claim)
            search_phrase = ' '.join(key_terms[:3])  # Use top 3 terms
            
            print(f"[FactCheckMatcherAgent] 🔍 Firecrawl searching for: '{search_phrase}' in fact-check sites")
            
            for site in factcheck_sites[:5]:  # Limit to top 5 sites for efficiency
                search_query = f'"{search_phrase}" {site}'
                
                url = "https://api.firecrawl.dev/v1/search"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "query": search_query,
                    "limit": 2,  # Limit per site to avoid overload
                    "lang": "en"
                }
                
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, headers=headers, json=data, timeout=10) as resp:  # Reduced from 15 to 10 seconds
                            if resp.status == 200:
                                results = await resp.json()
                                
                                if results and results.get('data'):
                                    for result in results['data']:
                                        # Calculate relevance score
                                        relevance = self._calculate_relevance(claim, result.get('description', ''))
                                        if relevance > 0.25:  # Lower threshold for fact-check sites
                                            match = {
                                                'source': self._extract_domain(result.get('url', '')),
                                                'url': result.get('url', ''),
                                                'title': result.get('title', ''),
                                                'main_claim': result.get('description', '')[:300] + '...',
                                                'rating': self._extract_rating_from_title(result.get('title', '')),
                                                'confidence': 'alto' if relevance > 0.5 else 'medio',
                                                'match_type': 'firecrawl_factcheck',
                                                'publish_date': '',
                                                'relevance_score': relevance
                                            }
                                            all_matches.append(match)
                            else:
                                print(f"[FactCheckMatcherAgent] Firecrawl error for {site}: {resp.status}")
                except Exception as e:
                    print(f"[FactCheckMatcherAgent] Error searching {site}: {e}")
                    continue
                
                # Reduced delay between requests for faster processing
                await asyncio.sleep(0.1)  # Reduced from 0.3 to 0.1 seconds
            
            # Sort by relevance and return top matches
            all_matches.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            print(f"[FactCheckMatcherAgent] 📊 Firecrawl found {len(all_matches)} relevant fact-check matches")
            return all_matches[:4]  # Top 4 most relevant
                        
        except Exception as e:
            print(f"[FactCheckMatcherAgent] Error in enhanced Firecrawl search: {e}")
            return []
    
    def _extract_rating_from_title(self, title: str) -> str:
        """Extract rating from fact-check title"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['false', 'fake', 'misleading', 'debunked']):
            return 'False'
        elif any(word in title_lower for word in ['true', 'correct', 'accurate']):
            return 'True'  
        elif any(word in title_lower for word in ['mixed', 'partly', 'partially']):
            return 'Mixed'
        else:
            return 'Unknown'
    
    def _extract_key_terms(self, claim: str) -> list:
        """Extract key terms from claim for better search"""
        import re
        
        # Remove common words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'that', 'this', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        
        # Extract words (alphanumeric, length > 3)
        words = re.findall(r'\b[a-zA-Z]{4,}\b', claim.lower())
        key_terms = [word for word in words if word not in stop_words]
        
        # Return top 5 terms for search
        return key_terms[:5]
    
    def _extract_domain(self, url: str) -> str:
        """Extract clean domain name from URL"""
        if not url:
            return 'Unknown'
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain.split('.')[0].title()
        except:
            return 'Unknown'
    
    def _calculate_relevance(self, claim: str, description: str) -> float:
        """Calculate relevance score between claim and description"""
        if not description:
            return 0.0
        
        claim_words = set(claim.lower().split())
        desc_words = set(description.lower().split())
        
        if not claim_words or not desc_words:
            return 0.0
        
        # Jaccard similarity
        intersection = claim_words.intersection(desc_words)
        union = claim_words.union(desc_words)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def _search_with_perplexity_enhanced(self, claim: str) -> list:
        """Enhanced Perplexity search using domain filters for fact-checkers"""
        try:
            import aiohttp
            
            api_key = os.environ.get("PERPLEXITY_API_KEY")
            if not api_key:
                print("[FactCheckMatcherAgent] No Perplexity API key found")
                return []
            
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Use domain filters to target only fact-checking sites
            fact_check_domains = [
                "snopes.com",
                "politifact.com", 
                "factcheck.org",
                "reuters.com",
                "apnews.com",
                "fullfact.org",
                "factcheckni.org",
                "checkyourfact.com"
            ]
            
            # Enhanced prompt specifically for fact-check discovery
            prompt = f"""
            Search for fact-checks and verification articles about this specific claim: "{claim}"
            
            Find:
            1. Direct fact-checks of this exact claim or very similar claims
            2. Verification articles that address the key facts mentioned
            3. Any contradictory or supporting evidence from reliable fact-checkers
            
            For each fact-check found, provide:
            - Source organization name
            - Verdict/rating (True, False, Mixed, Misleading, etc.)
            - Key findings summary
            - URL if available
            - How it relates to the original claim
            
            Focus on factual verification, not general news coverage.
            """
            
            data = {
                "model": "llama-3.1-sonar-large-128k-online",
                "messages": [{"role": "user", "content": prompt}],
                "search_domain_filter": fact_check_domains,  # This is the key improvement!
                "max_tokens": 600,
                "temperature": 0.1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=30) as resp:  # Reduced from 45 to 30 seconds
                    if resp.status == 200:
                        result = await resp.json()
                        content = result["choices"][0]["message"]["content"]
                        
                        print(f"[FactCheckMatcherAgent] 🎯 Perplexity with domain filters found content: {len(content)} chars")
                        
                        # Parse the response to extract structured fact-check results
                        return self._parse_perplexity_factcheck_response(content, claim)
                    else:
                        print(f"[FactCheckMatcherAgent] Perplexity API error: {resp.status}")
                        return []
                        
        except Exception as e:
            print(f"[FactCheckMatcherAgent] Error in enhanced Perplexity search: {e}")
            return []
    
    def _parse_perplexity_factcheck_response(self, content: str, original_claim: str) -> list:
        """Parse Perplexity response specifically for fact-check results"""
        matches = []
        
        # More sophisticated parsing for fact-check results
        import re
        
        # Look for structured fact-check patterns
        lines = content.split('\n')
        current_factcheck = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect fact-checker organizations
            factcheck_orgs = ['snopes', 'politifact', 'factcheck.org', 'reuters', 'ap news', 'full fact', 'afp', 'checkyourfact']
            
            if any(org in line.lower() for org in factcheck_orgs):
                # Save previous fact-check if exists
                if current_factcheck and current_factcheck.get('source'):
                    matches.append(current_factcheck)
                
                # Start new fact-check
                current_factcheck = {
                    'source': self._extract_factcheck_source(line),
                    'main_claim': line,
                    'rating': self._extract_factcheck_verdict(line),
                    'confidence': 'alto',
                    'match_type': 'perplexity_domain_filtered',
                    'url': self._extract_url_from_line(line),
                    'publish_date': '',
                    'relation_to_claim': 'direct'
                }
            
            # Look for verdict/rating patterns
            elif current_factcheck and any(verdict in line.lower() for verdict in ['true', 'false', 'mixed', 'misleading', 'unproven', 'correct', 'incorrect']):
                current_factcheck['rating'] = self._extract_factcheck_verdict(line)
                current_factcheck['main_claim'] += f" | {line}"
        
        # Add the last fact-check
        if current_factcheck and current_factcheck.get('source'):
            matches.append(current_factcheck)
        
        # If no structured matches found, create general results based on content
        if not matches and content and len(content) > 100:
            # Look for any mention of fact-checking results
            if any(word in content.lower() for word in ['false', 'true', 'misleading', 'verified', 'debunked', 'confirmed']):
                matches.append({
                    'source': 'Multiple Fact-Checkers',
                    'url': '',
                    'title': 'Fact-Check Search Results',
                    'main_claim': content[:400] + '...' if len(content) > 400 else content,
                    'rating': self._extract_overall_verdict(content),
                    'confidence': 'alto',
                    'match_type': 'perplexity_domain_analysis',
                    'publish_date': '',
                    'relation_to_claim': 'analysis'
                })
        
        print(f"[FactCheckMatcherAgent] 📊 Parsed {len(matches)} fact-check results from Perplexity")
        return matches[:5]  # Return top 5 results
    
    def _extract_factcheck_source(self, text: str) -> str:
        """Extract fact-checker source name"""
        factcheckers = {
            'snopes': 'Snopes',
            'politifact': 'PolitiFact', 
            'factcheck.org': 'FactCheck.org',
            'reuters': 'Reuters Fact Check',
            'ap news': 'AP Fact Check',
            'full fact': 'Full Fact',
            'afp': 'AFP Fact Check',
            'checkyourfact': 'Check Your Fact'
        }
        
        text_lower = text.lower()
        for key, name in factcheckers.items():
            if key in text_lower:
                return name
        return 'Fact-Checker'
    
    def _extract_factcheck_verdict(self, text: str) -> str:
        """Extract verdict from fact-check text"""
        verdicts = {
            'false': 'False',
            'true': 'True', 
            'mostly false': 'Mostly False',
            'mostly true': 'Mostly True',
            'mixed': 'Mixed',
            'misleading': 'Misleading',
            'unproven': 'Unproven',
            'correct': 'True',
            'incorrect': 'False',
            'debunked': 'False',
            'confirmed': 'True'
        }
        
        text_lower = text.lower()
        for key, verdict in verdicts.items():
            if key in text_lower:
                return verdict
        return 'Unknown'
    
    def _extract_overall_verdict(self, content: str) -> str:
        """Extract overall verdict from longer content"""
        content_lower = content.lower()
        
        # Count positive vs negative indicators
        negative_indicators = content_lower.count('false') + content_lower.count('misleading') + content_lower.count('debunked') + content_lower.count('incorrect')
        positive_indicators = content_lower.count('true') + content_lower.count('confirmed') + content_lower.count('verified') + content_lower.count('correct')
        
        if negative_indicators > positive_indicators:
            return 'Likely False'
        elif positive_indicators > negative_indicators:
            return 'Likely True'
        else:
            return 'Mixed/Unclear'
    
    def _extract_url_from_line(self, text: str) -> str:
        """Extract URL from a line of text"""
        import re
        url_pattern = r'https?://[^\s\)\]]+|www\.[^\s\)\]]+'
        urls = re.findall(url_pattern, text)
        return urls[0] if urls else ''
    
    async def _search_verified_media_sources(self, claim: str) -> list:
        """Search verified media sources when fact-checkers don't have coverage"""
        print(f"[FactCheckMatcherAgent] 📰 Searching verified media sources for: {claim[:50]}...")
        
        verified_sources = []
        
        # Lista de medios verificados y confiables
        trusted_media_domains = [
            "reuters.com", "apnews.com", "bbc.com", "npr.org",
            "theguardian.com", "nytimes.com", "washingtonpost.com",
            "cnn.com", "nbcnews.com", "cbsnews.com", "abcnews.go.com",
            "bloomberg.com", "wsj.com", "usatoday.com"
        ]
        
        try:
            # Usar Firecrawl para búsqueda en medios verificados
            from adk_project.utils.firecrawl import firecrawl_search_tool
            
            # Crear query específica para búsqueda de verificación
            search_query = f'"{claim}" OR "{claim.split()[0]} {claim.split()[-1]}" site:reuters.com OR site:apnews.com OR site:bbc.com OR site:npr.org'
            
            print(f"[FactCheckMatcherAgent] 🔍 Searching with query: {search_query[:100]}...")
            
            # Búsqueda usando Firecrawl
            search_results = await firecrawl_search_tool(search_query, limit=10)
            
            if search_results and isinstance(search_results, list):
                for result in search_results[:5]:  # Limitar a 5 resultados
                    if isinstance(result, dict):
                        url = result.get('url', '')
                        title = result.get('title', '')
                        description = result.get('description', '')
                        
                        # Verificar si es de un medio confiable
                        is_trusted = any(domain in url.lower() for domain in trusted_media_domains)
                        
                        if is_trusted and title:
                            verified_sources.append({
                                'source': 'Verified Media',
                                'url': url,
                                'headline': title,
                                'main_claim': description or title,
                                'rating': 'Media Coverage',
                                'relevance_score': self._calculate_relevance(claim, title + ' ' + description),
                                'source_type': 'verified_media',
                                'domain': next((d for d in trusted_media_domains if d in url.lower()), 'unknown')
                            })
            
            # Si no hay suficientes resultados, intentar búsqueda más específica
            if len(verified_sources) < 3:
                print(f"[FactCheckMatcherAgent] 🔍 Expanding search to more sources...")
                
                # Búsqueda más específica por keywords principales
                main_keywords = self._extract_main_keywords(claim)
                expanded_query = f'{" ".join(main_keywords)} verified OR confirmed OR official'
                
                expanded_results = await firecrawl_search_tool(expanded_query, limit=8)
                
                if expanded_results and isinstance(expanded_results, list):
                    for result in expanded_results[:3]:
                        if isinstance(result, dict):
                            url = result.get('url', '')
                            title = result.get('title', '')
                            description = result.get('description', '')
                            
                            is_trusted = any(domain in url.lower() for domain in trusted_media_domains)
                            
                            if is_trusted and title and url not in [vs['url'] for vs in verified_sources]:
                                verified_sources.append({
                                    'source': 'Verified Media Expanded',
                                    'url': url,
                                    'headline': title,
                                    'main_claim': description or title,
                                    'rating': 'Media Coverage',
                                    'relevance_score': self._calculate_relevance(claim, title + ' ' + description),
                                    'source_type': 'verified_media_expanded',
                                    'domain': next((d for d in trusted_media_domains if d in url.lower()), 'unknown')
                                })
            
            print(f"[FactCheckMatcherAgent] ✅ Found {len(verified_sources)} verified media sources")
            return verified_sources[:5]  # Máximo 5 fuentes
            
        except Exception as e:
            print(f"[FactCheckMatcherAgent] ❌ Error in verified media search: {e}")
            return []
    
    def _extract_main_keywords(self, claim: str) -> list:
        """Extract main keywords from claim for targeted search"""
        import re
        
        # Remover palabras comunes
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        
        # Extraer palabras importantes (más de 3 letras, no stop words)
        words = re.findall(r'\b\w{4,}\b', claim.lower())
        keywords = [word for word in words if word not in stop_words]
        
        return keywords[:5]  # Máximo 5 keywords principales
    
    def _calculate_relevance(self, claim: str, content: str) -> float:
        """Calculate relevance score between claim and content"""
        import re
        
        claim_words = set(re.findall(r'\b\w+\b', claim.lower()))
        content_words = set(re.findall(r'\b\w+\b', content.lower()))
        
        if not claim_words or not content_words:
            return 0.0
        
        intersection = claim_words.intersection(content_words)
        union = claim_words.union(content_words)
        
        return len(intersection) / len(union) if union else 0.0
