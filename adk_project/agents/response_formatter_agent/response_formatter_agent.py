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

    def _score_to_label_and_fraction(self, score: int) -> tuple:
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

    def _format_verified_sources(self, sources: list, matches_data: dict = None) -> list:
        """Formatea las fuentes verificadas - solo incluye fuentes con similitud real"""
        verified = []
        
        # Usar las fuentes que ya fueron filtradas por similitud por el truth_scorer
        for source in sources[:6]:  # Limitar a 6 fuentes como en la imagen
            if isinstance(source, str) and source.startswith('http'):
                # Es una URL directa, buscar información adicional en matches si está disponible
                name = "Fact-checker verificado"
                url = source
                description = "Fuente que verificó contenido relacionado"
                
                # Intentar obtener más información de los matches
                if matches_data and 'matches' in matches_data:
                    for match in matches_data['matches']:
                        if match.get('url') == source:
                            name = match.get('headline', match.get('title', 'Fact-checker verificado'))
                            description = f"Verificación: {match.get('verdict', match.get('rating', 'Contenido relacionado'))}"
                            break
                            
            elif isinstance(source, dict):
                name = source.get('title', source.get('name', source.get('headline', 'Fuente verificada')))
                url = source.get('url', '#')
                description = source.get('description', source.get('verdict', source.get('rating', '')))
            else:
                name = "Fuente verificada"
                url = str(source) if source else '#'
                description = "Contenido verificado"
            
            # Solo agregar si tiene URL válida (evitar placeholders)
            if url and url != '#' and url.startswith('http'):
                verified.append(VerifiedSource(name=name, url=url, description=description))
        
        return verified

    def _generate_recommendation(self, score: int, main_claim: str, detailed_analysis: str, fact_check_results: dict = None) -> str:
        """Generate contextual professional recommendation based on analysis"""
        try:
            # Configure Gemini
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            # Get match quality information
            match_quality = fact_check_results.get('match_quality', 'weak') if fact_check_results else 'unknown'
            confidence_level = fact_check_results.get('confidence_level', 'low') if fact_check_results else 'low'
            matches = fact_check_results.get('matches', []) if fact_check_results else []
            
            prompt = f"""
            Generate a professional recommendation (2-3 sentences max) in English for users about this fact-check result.
            
            CLAIM EVALUATED: {main_claim}
            ANALYSIS SCORE: {score}/5
            DETAILED ANALYSIS: {detailed_analysis}
            MATCH QUALITY: {match_quality} 
            CONFIDENCE: {confidence_level}
            SOURCES FOUND: {len(matches)}
            
            Requirements:
            - Be specific about the verification status and what it means for users
            - Provide actionable advice based on the score and evidence quality
            - Professional tone, English only
            - Maximum 3 sentences
            - Focus on practical guidance for users about trusting/using this information
            - Avoid generic statements; be specific to this case
            
            Examples of good recommendations:
            - "Strong verification from multiple fact-checkers confirms this claim's accuracy; you can confidently cite this information."
            - "Limited fact-check coverage and mixed evidence suggest treating this claim cautiously until additional verification emerges."
            - "No professional fact-check coverage found; verify independently through primary sources before accepting or sharing."
            """
            
            response = model.generate_content(prompt)
            recommendation = response.text.strip()
            return recommendation
            
        except Exception as e:
            print(f"Error generating recommendation with Gemini: {e}")
            return self._generate_fallback_recommendation(score, main_claim, len(matches) if matches else 0)
            return self._generate_fallback_recommendation(score, main_claim, len(matches) if matches else 0)
    
    def _generate_fallback_recommendation(self, score: int, main_claim: str, num_sources: int) -> str:
        """Generate fallback recommendation based on score and sources"""
        if score >= 4 and num_sources >= 2:
            return f"Strong verification from {num_sources} sources confirms this claim's reliability; you can confidently reference this information."
        elif score >= 3 and num_sources >= 1:
            return f"Moderate verification suggests this claim is largely accurate, though cross-referencing with additional sources is recommended."
        elif score == 2:
            return f"Mixed evidence requires careful consideration; verify through primary sources before accepting or sharing this claim."
        elif score == 1:
            return f"Limited verification available; treat this claim with caution and seek additional authoritative sources."
        else:
            return f"Insufficient evidence to verify this claim; independent verification through multiple reliable sources is essential."
    
    
    def _generate_media_literacy_tip(self, score: int, main_claim: str, article_domain: str) -> str:
        """Generate brief contextual media literacy tip in English"""
        try:
            # Configure Gemini
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            prompt = f"""
            Generate a VERY brief media literacy tip (MAXIMUM 30 words) in English for this specific case.

            CLAIM: "{main_claim}"
            SOURCE: {article_domain}
            SCORE: {score}/5

            Requirements:
            - Professional tone, English only
            - MAXIMUM 30 words
            - Single sentence preferred
            - Specific to this type of content
            - Educational, not generic
            - Focus on verification methods
            """
            
            response = model.generate_content(prompt)
            tip = response.text.strip()
            return tip
            
        except Exception as e:
            print(f"Error generating media literacy tip with Gemini: {e}")
            return self._generate_contextual_fallback_tip(main_claim, article_domain, score)

    def _generate_contextual_fallback_tip(self, main_claim: str, domain: str, score: int) -> str:
        """Generate brief contextual fallback tip in English (max 30 words)"""
        claim_lower = main_claim.lower()
        
        # Analysis by content type
        if any(word in claim_lower for word in ['study', 'research', 'scientists']):
            return "For scientific claims, verify peer-reviewed publication and check methodology details."
            
        elif any(word in claim_lower for word in ['government', 'officials', 'minister']):
            return "For official statements, cross-reference with government channels and verify context."
            
        elif any(word in claim_lower for word in ['violence', 'killed', 'injured', 'attack']):
            return "For crisis events, verify with official sources and multiple independent reports."
            
        elif any(word in claim_lower for word in ['economic', 'price', 'cost', 'inflation']):
            return "For economic data, verify with official statistical institutions and check methodology."
            
        else:
            if score <= 2:
                return "Low credibility: Apply SIFT method - Stop, Investigate source, Find coverage, Trace origin."
            else:
                return "Practice lateral verification: check source reputation and cross-reference with established outlets."

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
        
        # Score y etiquetas (asegurar que sea siempre un entero)
        raw_score = scored.get('score', 2)
        score = int(raw_score) if isinstance(raw_score, (int, float, str)) and str(raw_score).replace('.', '').isdigit() else 2
        score_label, score_fraction = self._score_to_label_and_fraction(score)
        
        # Main claim
        main_claim = extracted_claim.get('claim', '') or scored.get('main_claim', '')
        
        # Análisis detallado
        detailed_analysis = scored.get('detailed_analysis', 'No hay análisis detallado disponible.')
        
        # Fuentes verificadas (con datos de matches para contexto)
        verified_sources = self._format_verified_sources(scored.get('verified_sources', []), matches)
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
        
        # Determinar tipo de match del análisis
        match_type = scored.get('match_type', 'tangential')
        
        # Crear respuesta estructurada
        agui_response = AGUIResponse(
            headline=headline,
            url=url,
            source_domain=domain,
            score=score,
            score_label=score_label,
            score_fraction=score_fraction,
            main_claim=main_claim,
            detailed_analysis=self._generate_recommendation(score, main_claim, detailed_analysis, matches),
            verified_sources=verified_sources,
            verified_sources_label=verified_sources_label,
            match_type=match_type,
            recommendation=self._generate_recommendation(score, main_claim, detailed_analysis, matches),
            media_literacy_tip=self._generate_media_literacy_tip(score, main_claim, domain),
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
