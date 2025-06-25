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

    def _format_verified_sources(self, sources: list) -> list:
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

    def _generate_recommendation(self, score: int, main_claim: str, detailed_analysis: str, fact_check_results: dict = None) -> str:
        """Generate contextual analysis based on match quality and findings"""
        try:
            # Configure Gemini
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            # Get match quality information
            match_quality = fact_check_results.get('match_quality', 'weak') if fact_check_results else 'unknown'
            confidence_level = fact_check_results.get('confidence_level', 'low') if fact_check_results else 'low'
            matches = fact_check_results.get('matches', []) if fact_check_results else []
            
            # Determine analysis tone based on match quality
            if match_quality == 'strong' and confidence_level == 'high':
                analysis_tone = "conclusive"
            elif match_quality == 'moderate' and confidence_level in ['medium', 'high']:
                analysis_tone = "moderate"
            else:
                analysis_tone = "cautious"
            
            prompt = f"""
            Generate a brief professional analysis (1-2 sentences max) in English about this claim's credibility.
            
            CLAIM: {main_claim}
            SCORE: {score}/5
            MATCH QUALITY: {match_quality} 
            CONFIDENCE: {confidence_level}
            MATCHES FOUND: {len(matches)}
            
            ANALYSIS TONE REQUIRED: {analysis_tone}
            
            Guidelines:
            - If CONCLUSIVE: Be definitive about the claim's truth value based on strong fact-check matches
            - If MODERATE: Be measured, mention limitations, suggest additional verification
            - If CAUTIOUS: Be very careful, emphasize lack of clear verification, avoid strong conclusions
            
            Requirements:
            - Professional tone, English only
            - Maximum 2 sentences
            - Match the required analysis tone
            - Be specific about verification status
            """
            
            response = model.generate_content(prompt)
            analysis = response.text.strip()
            return analysis
            
        except Exception as e:
            print(f"Error generating analysis with Gemini: {e}")
            return self._generate_fallback_analysis_by_quality(score, main_claim, match_quality if 'match_quality' in locals() else 'weak', len(matches) if 'matches' in locals() else 0)
    
    def _generate_fallback_analysis_by_quality(self, score: int, main_claim: str, match_quality: str, num_matches: int) -> str:
        """Generate fallback analysis based on match quality"""
        
        if match_quality == 'strong':
            if score <= 2:
                return f"Based on {num_matches} strong fact-check matches, this claim is demonstrably false."
            elif score >= 4:
                return f"Strong verification from {num_matches} fact-checkers confirms this claim's accuracy."
            else:
                return f"Multiple fact-checkers provide mixed but conclusive evidence about this claim."
        
        elif match_quality == 'moderate':
            return f"Limited fact-check coverage found; score {score}/5 suggests caution and additional verification needed."
        
        else:  # weak or unknown
            return f"Insufficient fact-check coverage for definitive assessment; score {score}/5 based on available indicators."

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
            detailed_analysis=self._generate_recommendation(score, main_claim, detailed_analysis, matches),
            verified_sources=verified_sources,
            verified_sources_label=verified_sources_label,
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
