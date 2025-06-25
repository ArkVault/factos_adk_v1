from google.adk.agents import LlmAgent
from adk_project.agents.response_formatter_agent.prompt import FORMATTER_PROMPT
from adk_project.protocols.agui_response import AGUIResponse, VerifiedSource, SourceCredibility, AnalysisStats
import asyncio
import os
import time
from urllib.parse import urlparse
from adk_project.utils.firecrawl import firecrawl_search_tool
import google.generativeai as genai

class ResponseFormatterAgent(LlmAgent):
    def __init__(self):
        super().__init__(
            name="ResponseFormatterAgent",
            instruction=(
                "Eres un experto en formatear resultados de fact-checking para interfaces de usuario. "
                "Tu trabajo es tomar los datos del análisis y crear una respuesta estructurada y clara "
                "que coincida exactamente con el formato esperado por el frontend. "
                "\n\nDebes:"
                "\n1. Extraer el headline del artículo original"
                "\n2. Convertir el score numérico a etiquetas descriptivas"
                "\n3. Formatear las fuentes verificadas con enlaces"
                "\n4. Crear recomendaciones claras y tips educativos"
                "\n5. Evaluar la credibilidad de la fuente original"
                "\n6. Incluir estadísticas del análisis"
            ),
            description="Formatea resultados de fact-checking en estructura AG-UI compatible.",
            output_key="agui_response",
            model="gemini-2.5-flash"
        )

    def _extract_headline_from_content(self, content: str) -> str:
        """Extrae el headline principal del contenido markdown"""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# ') and len(line) > 10:
                return line[2:].strip()
            elif line.startswith('## ') and len(line) > 10:
                return line[3:].strip()
        
        # Fallback: buscar líneas que parezcan headlines
        for line in lines:
            line = line.strip()
            if len(line) > 20 and len(line) < 200 and not line.startswith('['):
                return line
        
        return "Artículo de noticias"

    def _score_to_label_and_fraction(self, score: int) -> tuple[str, str]:
        """Convierte score numérico a etiqueta y fracción"""
        score_map = {
            0: ("False", "0/5 • Completely false"),
            1: ("Mostly False", "1/5 • Mostly false"), 
            2: ("Mixed", "2/5 • Context needed"),
            3: ("Mostly True", "3/5 • Mostly true"),
            4: ("True", "4/5 • Mostly true"),
            5: ("True", "5/5 • Completely true")
        }
        return score_map.get(score, ("Unknown", f"{score}/5 • Unknown"))

    def _assess_source_credibility(self, url: str) -> SourceCredibility:
        """Evalúa la credibilidad de la fuente original"""
        domain = urlparse(url).netloc.lower()
        
        # Fuentes de alta confianza
        high_trust = [
            'apnews.com', 'reuters.com', 'bbc.com', 'npr.org',
            'theguardian.com', 'nytimes.com', 'washingtonpost.com'
        ]
        
        # Fuentes de confianza media
        medium_trust = [
            'cnn.com', 'foxnews.com', 'nbcnews.com', 'cbsnews.com',
            'abc.com', 'usatoday.com', 'bloomberg.com'
        ]
        
        if any(trusted in domain for trusted in high_trust):
            return SourceCredibility("High Trust", "Low", domain)
        elif any(medium in domain for medium in medium_trust):
            return SourceCredibility("Medium Trust", "Medium", domain)
        else:
            return SourceCredibility("Medium Risk", "Medium", domain)

    def _format_verified_sources(self, sources: list) -> list[VerifiedSource]:
        """Formatea las fuentes verificadas"""
        verified = []
        for source in sources[:6]:  # Limitar a 6 fuentes como en la imagen
            if isinstance(source, dict):
                name = source.get('title', source.get('name', 'Fuente verificada'))
                url = source.get('url', '#')
                description = source.get('description', '')
            else:
                name = "Fuente verificada"
                url = str(source) if source else '#'
                description = ""
            
            verified.append(VerifiedSource(name=name, url=url, description=description))
        
        return verified

    def _generate_recommendation(self, score: int, main_claim: str, detailed_analysis: str) -> str:
        """Genera recomendación basada en el análisis"""
        if score <= 1:
            return f"Correction: {detailed_analysis[:200]}..."
        elif score == 2:
            return f"Context needed: {detailed_analysis[:200]}..."
        else:
            return f"Verification: {detailed_analysis[:200]}..."

    def _generate_media_literacy_tip(self, score: int) -> str:
        """Genera tip de alfabetización mediática"""
        tips = {
            0: "Be wary of headlines claiming dramatic health benefits without specifying study limitations or population groups.",
            1: "Look for peer-reviewed sources and check if studies have been replicated by independent researchers.",
            2: "When claims seem too good to be true, verify the methodology and sample size of the original research.",
            3: "Cross-reference health claims with established medical institutions and health organizations.",
            4: "Even accurate information can be presented misleadingly - always read the full context.",
            5: "Verify information through multiple reputable sources before sharing health-related content."
        }
        return tips.get(score, "Always verify information through multiple reputable sources.")

    async def run_async(self, ctx):
        """Formatea la respuesta final siguiendo la estructura exacta de la imagen"""
        state = ctx.session.state
        start_time = time.time()
        
        # Extraer datos de los agentes anteriores
        scored = state.get('scored_result', {})
        article = state.get('validated_article', {})
        matches = state.get('match_results', {})
        extracted_claim = state.get('extracted_claim', {})
        
        # Datos del artículo
        url = state.get('input', '')
        content = article.get('data', {}).get('markdown', '') if article.get('data') else ''
        headline = self._extract_headline_from_content(content)
        domain = urlparse(url).netloc
        
        # Score y etiquetas
        score = scored.get('score', 2)
        score_label, score_fraction = self._score_to_label_and_fraction(score)
        
        # Main claim
        main_claim = extracted_claim.get('claim', '') or scored.get('main_claim', '')
        
        # Análisis detallado
        detailed_analysis = scored.get('detailed_analysis', 'No hay análisis detallado disponible.')
        
        # Fuentes verificadas
        verified_sources = self._format_verified_sources(scored.get('verified_sources', []))
        verified_sources_label = "High Trust" if len(verified_sources) >= 3 else "Medium Trust"
        
        # Credibilidad de la fuente
        source_credibility = self._assess_source_credibility(url)
        
        # Estadísticas
        processing_time = time.time() - start_time
        analysis_stats = AnalysisStats(
            processing_time=round(processing_time, 1),
            sources_checked=len(verified_sources),
            confidence_level=scored.get('confidence_level', 60)
        )
        
        # Crear respuesta estructurada
        agui_response = AGUIResponse(
            headline=headline,
            url=url,
            source_domain=domain,
            score=score,
            score_label=score_label,
            score_fraction=score_fraction,
            main_claim=main_claim,
            detailed_analysis=detailed_analysis,
            verified_sources=verified_sources,
            verified_sources_label=verified_sources_label,
            recommendation=self._generate_recommendation(score, main_claim, detailed_analysis),
            media_literacy_tip=self._generate_media_literacy_tip(score),
            source_credibility=source_credibility,
            analysis_stats=analysis_stats,
            active_agents=[
                {"name": "Fact-Check Agent", "status": "Active"},
                {"name": "Source Finder", "status": "Active"},
                {"name": "Media Literacy Coach", "status": "Active"}
            ],
            quick_actions={
                "share_analysis": True,
                "save_report": True
            }
        )
        
        # Guardar en el estado como diccionario para compatibilidad
        ctx.session.state["agui_response"] = agui_response.to_dict()
        
        yield
            "recommendation": scored.get("recommendation", ""),
            "media_literacy_tip": scored.get("media_literacy_tip", ""),
            "processing_time": scored.get("processing_time", 0.0),
            "confidence_level": scored.get("confidence_level", 0),
            "sources_checked": len(matches),
            "original_source_label": "Medium Risk",  # Always in English
            "original_source_url": article.get("url", ""),
            "verified_sources_label": "High Trust"  # Always in English
        }
        # 1. Recommendation y media_literacy_tip más contextuales
        if matches:
            recommendation = "Based on related fact-checks, review the following sources for verification and context."
            media_literacy_tip = "Compare the main claim with the headlines and conclusions of the fact-checkers listed."
        else:
            recommendation = "No direct fact-checks found, but similar topics were identified. Review the closest matches and consider the credibility of the sources."
            media_literacy_tip = "If no direct match is found, look for similar claims in reputable fact-checking sites and cross-reference information."
        agui_response["recommendation"] = recommendation
        agui_response["media_literacy_tip"] = media_literacy_tip
        # 2. detailed_analysis con Gemini
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        if matches:
            context_text = "\n".join([f"Headline: {c['headline']}\nClaim: {c['main_claim']}" for c in matches[:3]])
            prompt = f"Analyze the following fact-checks and briefly assess the plausibility of the main claim based on these sources.\nClaim: {scored.get('main_claim', '')}\nFact-checks:\n{context_text}"
            detailed_analysis = model.generate_content(prompt).text
        else:
            # 3. Si no hay fact-checkers directos, buscar en otros sitios verificados
            fallback_domains = [
                "snopes.com", "fullfact.org", "factcheck.org", "reuters.com", "politifact.com", "bbc.com", "washingtonpost.com"
            ]
            firecrawl_results = await firecrawl_search_tool(scored.get('main_claim', ''), fallback_domains, limit=5, include_subdomains=True, similarity_threshold=60)
            context_text = "\n".join([f"Headline: {r.get('title', '')}\nClaim: {r.get('markdown', '')[:200]}" for r in firecrawl_results.get('results', [])])
            prompt = f"Given the following related fact-checks from reputable sources, briefly assess the plausibility of the main claim.\nClaim: {scored.get('main_claim', '')}\nFact-checks:\n{context_text}"
            detailed_analysis = model.generate_content(prompt).text
        agui_response["detailed_analysis"] = detailed_analysis
        state["agui_response"] = agui_response
        yield  # Para cumplir con la interfaz async

    def generate_agui_response(claim, claims_found, original_url, factchecker_domains, fallback_domains=None):
        # Inicializar modelo Gemini
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        perplexity_used = False
        # 1. Priorizar fact-checkers: si hay claims_found de la lista prioritaria, usarlos primero
        if claims_found:
            recommendation = "Based on related fact-checks from trusted fact-checkers, review the following sources for verification and context."
            media_literacy_tip = "Compare the main claim with the headlines and conclusions of the prioritized fact-checkers listed."
            context_text = "\n".join([f"Headline: {c['headline']}\nClaim: {c['main_claim']}" for c in claims_found[:3]])
            prompt = f"Analyze the following fact-checks from trusted fact-checkers and briefly assess the plausibility of the main claim based on these sources.\nClaim: {claim}\nFact-checks:\n{context_text}"
            detailed_analysis = model.generate_content(prompt).text
        else:
            # 2. Si no hay matches suficientemente relacionados en fact-checkers, usar medios alternativos verificados
            recommendation = "No direct fact-checks found in main fact-checkers, but similar topics were identified in other reputable sources. Review the closest matches and consider the credibility of the sources."
            media_literacy_tip = "If no direct match is found in main fact-checkers, look for similar claims in reputable fact-checking sites and cross-reference information."
            fallback_domains = fallback_domains or [
                "snopes.com", "fullfact.org", "factcheck.org", "reuters.com", "politifact.com", "bbc.com", "washingtonpost.com"
            ]
            firecrawl_results = asyncio.run(firecrawl_search_tool(claim, fallback_domains, limit=5, include_subdomains=True, similarity_threshold=60))
            context_text = "\n".join([f"Headline: {r.get('title', '')}\nClaim: {r.get('markdown', '')[:200]}" for r in firecrawl_results.get('results', [])])
            if not firecrawl_results.get('results'):
                perplexity_api_key = os.environ.get("PERPLEXITY_API_KEY")
                sonar_content = perplexity_sonar_search(claim, perplexity_api_key, domains=fallback_domains)
                context_text = sonar_content
                perplexity_used = True
            prompt = f"Based on the following information from official news channels and fact-checkers, briefly assess the plausibility of the main claim.\nClaim: {claim}\nFact-checks:\n{context_text}"
            detailed_analysis = model.generate_content(prompt).text
        # 1. Main claim: resumido y limpio
        def clean_main_claim(text):
            import re
            # Elimina links, markdown y deja solo una frase breve
            text = re.sub(r'\[.*?\]\(.*?\)', '', text)  # elimina markdown links
            text = re.sub(r'[^\w\s.,\'-]', '', text)  # elimina caracteres raros
            text = text.strip()
            # Limita a 200 caracteres o primer punto
            if '.' in text:
                text = text.split('.')[0] + '.'
            return text[:200]
        # 2. detailed_analysis: solo un párrafo breve sobre verosimilitud
        def brief_analysis(text):
            # Limita a 2-3 frases, elimina listas y explicaciones largas
            import re
            text = re.sub(r'\*\*.*?\*\*', '', text)  # elimina markdown bold
            text = re.sub(r'\n+', ' ', text)
            text = text.strip()
            sentences = text.split('.')
            return '. '.join(sentences[:2]).strip() + '.'
        # 3. recommendation: juicio de calidad del medio
        def media_quality_recommendation(source_label):
            if source_label == 'High Trust':
                return "This news comes from a highly reputable source."
            elif source_label == 'Medium Risk':
                return "This news comes from a generally reliable source, but cross-check with other outlets is advised."
            else:
                return "Source credibility is unclear. Seek confirmation from trusted media."
        # 4. media_literacy_tip: sugerir atención a datos concretos
        def factual_tip():
            return "Pay attention to concrete data, direct quotes, and verifiable facts in the article."
        # Armar respuesta final
        agui_response = {
            "headline": claims_found[0]["headline"] if claims_found else "",
            "url": claims_found[0]["url"] if claims_found else "",
            "score": claims_found[0]["score"] if claims_found else 2,
            "score_label": claims_found[0]["report"] if claims_found else "Context Needed",
            "main_claim": clean_main_claim(claim),
            "detailed_analysis": brief_analysis(detailed_analysis),
            "verified_sources": [],
            "recommendation": media_quality_recommendation("High Trust" if claims_found else "Medium Risk"),
            "media_literacy_tip": factual_tip(),
            "processing_time": 0.0,
            "confidence_level": 60,
            "sources_checked": len(claims_found),
            "original_source_label": "High Trust" if claims_found else "Medium Risk",
            "original_source_url": original_url,
            "verified_sources_label": "High Trust" if claims_found else "Medium Risk",
            "perplexity_used": perplexity_used
        }
        print(f"[AGUI] Perplexity Sonar used: {perplexity_used}")
        return agui_response

    def perplexity_sonar_search(query, api_key, domains=None):
        """
        Realiza una búsqueda en Perplexity Sonar restringida a dominios si se proveen, usando search_domain_filter.
        """
        url = "https://api.perplexity.ai/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "sonar-reasoning-pro",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": query}
            ]
        }
        if domains:
            # Limitar a máximo 10 dominios, usar solo el dominio base sin https ni www
            payload["search_domain_filter"] = [d.replace("https://","").replace("http://","").replace("www.","").split("/")[0] for d in domains][:10]
        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        if resp.status_code == 200:
            # El resultado relevante está en response["choices"][0]["message"]["content"]
            try:
                return resp.json()["choices"][0]["message"]["content"]
            except Exception:
                return ""
        return []
