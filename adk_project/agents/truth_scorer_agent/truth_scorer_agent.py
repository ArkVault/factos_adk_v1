from google.adk.agents import LlmAgent
from adk_project.agents.truth_scorer_agent.prompt import TRUTH_SCORER_PROMPT

TRUTH_SCORER_OUTPUT_SCHEMA = {
    "score": "int (0-3)",
    "label": "str (e.g. 'False', 'True', 'Misleading', 'Context Needed')",
    "main_claim": "str",
    "detailed_analysis": "str",
    "verified_sources": "list[str]",
    "recommendation": "str (opcional)",
    "media_literacy_tip": "str (opcional)",
    "confidence_level": "int (opcional)",
    "processing_time": "float (opcional)"
}

class TruthScorerAgent(LlmAgent):
    def __init__(self):
        super().__init__(
            name="TruthScorerAgent",
            instruction=TRUTH_SCORER_PROMPT + "\n\nTu respuesta debe ser un JSON con la siguiente estructura: " + str(TRUTH_SCORER_OUTPUT_SCHEMA),
            description="Asigna un puntaje de desinformación y explica el resultado en formato estructurado para el frontend.",
            output_key="scored_result",
            model="gemini-2.5-flash"
        )

    async def run_async(self, ctx):
        import time
        import json
        claim = ctx.session.state.get("extracted_claim", {}).get("claim", "")
        matches = ctx.session.state.get("match_results", {}).get("matches", [])
        start = time.time()
        
        if not claim:
            ctx.session.state["scored_result"] = {}
            yield
            return

        # Preparar contexto para el análisis profesional
        context = {
            "claim": claim,
            "num_matches": len(matches),
            "matches_summary": []
        }
        
        # Resumir las coincidencias encontradas, separando por tipo de fuente
        factcheck_matches = []
        verified_media_matches = []
        
        for i, match in enumerate(matches[:5]):  # Analizar hasta 5 coincidencias
            match_summary = {
                "source": match.get("source", "Unknown source"),
                "url": match.get("url", ""),
                "headline": match.get("headline", match.get("main_claim", match.get("title", "No title available"))),
                "fact_check_rating": match.get("rating", match.get("verdict", match.get("fact_check_result", "unknown"))),
                "relevance": match.get("relevance_score", "unknown"),
                "confidence": match.get("confidence", "unknown"),
                "match_type": match.get("match_type", "unknown"),
                "relation_type": match.get("relation_type", "unknown"),
                "semantic_explanation": match.get("semantic_explanation", ""),
                "publish_date": match.get("publish_date", ""),
                "author": match.get("author", ""),
                "content_snippet": match.get("content", match.get("description", ""))[:200] + "..." if match.get("content", match.get("description", "")) else "",
                "source_type": match.get("source_type", "factcheck"),
                "domain": match.get("domain", "")
            }
            
            # Categorizar por tipo de fuente
            if match.get("source_type") in ["verified_media", "verified_media_expanded"]:
                verified_media_matches.append(match_summary)
            else:
                factcheck_matches.append(match_summary)
        
        context["factcheck_matches"] = factcheck_matches
        context["verified_media_matches"] = verified_media_matches
        context["total_factcheck_matches"] = len(factcheck_matches)
        context["total_verified_media_matches"] = len(verified_media_matches)

        # Extraer URL original para análisis de credibilidad
        original_url = ctx.session.state.get("validated_article", {}).get("url", "")
        
        # Construir prompt para análisis profesional
        analysis_prompt = f"""
        Como experto verificador de hechos, analiza la veracidad de una afirmación considerando TANTO la credibilidad de la fuente original COMO las verificaciones encontradas.

        FUENTE ORIGINAL: {original_url}
        
        AFIRMACIÓN A EVALUAR: 
        "{claim}"
        
        VERIFICACIONES ENCONTRADAS EN FACT-CHECKERS PROFESIONALES:
        {json.dumps(context["factcheck_matches"], indent=2, ensure_ascii=False) if context["factcheck_matches"] else "No se encontraron coincidencias directas en fact-checkers profesionales"}
        
        COBERTURA EN MEDIOS VERIFICADOS:
        {json.dumps(context["verified_media_matches"], indent=2, ensure_ascii=False) if context["verified_media_matches"] else "No se encontró cobertura en medios verificados principales"}
        
        METADATOS DE BÚSQUEDA:
        - Fact-checkers encontrados: {context["total_factcheck_matches"]}
        - Medios verificados encontrados: {context["total_verified_media_matches"]}
        - Calidad de coincidencias: {ctx.session.state.get("match_results", {}).get("match_quality", "unknown")}
        - Nivel de confianza en búsqueda: {ctx.session.state.get("match_results", {}).get("confidence_level", "unknown")}
        - Método de búsqueda: {ctx.session.state.get("match_results", {}).get("search_method", "unknown")}

        INSTRUCCIONES PARA EL ANÁLISIS:
        1. PRIORIZA las verificaciones de fact-checkers profesionales (mayor peso evidencial)
        2. USA cobertura de medios verificados como contexto de apoyo
        3. Examina la relación semántica entre la afirmación y cada fuente
        4. Considera la calidad, relevancia y credibilidad de cada fuente
        5. Evalúa si hay consenso entre las fuentes o contradicciones
        
        CRITERIOS DE PUNTUACIÓN MEJORADOS (0-5):
        - CONSIDERA PRIMERO la credibilidad de la fuente original
        - Si fuente es altamente confiable (BBC, Reuters, AP, etc.) Y no hay contradicciones directas: MÍNIMO score 3
        - Solo usa scores bajos (0-2) cuando hay evidencia DIRECTA de fact-checkers contradiciendo
        - Distingue entre "no verificado" vs "verificado como falso"
        
        ANÁLISIS DE CREDIBILIDAD DE FUENTE:
        Evalúa la URL original para determinar credibilidad base:
        - Tier 1 (muy confiable): Reuters, AP, BBC, NPR, PBS
        - Tier 2 (confiable): Guardian, NYT, Washington Post, CNN, ABC, CBS, NBC
        - Tier 3 (moderadamente confiable): Otros medios establecidos
        - Tier 4 (verificar): Medios menos conocidos o especializados
        
        FORMATO DE RESPUESTA REQUERIDO (JSON válido):
        {{
            "score": [número 0-5, considerando credibilidad de fuente original],
            "label": "[etiqueta basada en evidencia real, no en ausencia de evidencia]",
            "main_claim": "{claim}",
            "detailed_analysis": "[análisis profesional de 2-3 oraciones mencionando: 1) credibilidad de fuente original, 2) tipo y calidad de verificaciones encontradas, 3) razonamiento específico para la puntuación asignada]",
            "verified_sources": [lista de URLs SOLO de fuentes que tienen similitud real con la afirmación],
            "match_type": "[direct/derivative/tangential]",
            "recommendation": "[recomendación específica considerando tanto la fuente original como las verificaciones]",
            "media_literacy_tip": "[consejo específico para este tipo de fuente y verificaciones disponibles]",
            "confidence_level": [0-100],
            "processing_time": {round(time.time() - start, 2)}
        }}"""

        try:
            # Usar el LLM para análisis profesional
            response = await self._generate_with_llm(analysis_prompt, ctx)
            
            # Intentar parsear la respuesta JSON
            if response and response.strip().startswith('{'):
                try:
                    result = json.loads(response.strip())
                    # Validar que tenga los campos requeridos
                    if all(key in result for key in ["score", "label", "main_claim", "detailed_analysis"]):
                        ctx.session.state["scored_result"] = result
                    else:
                        raise ValueError("Missing required fields")
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Error parsing LLM response: {e}")
                    ctx.session.state["scored_result"] = self._generate_fallback_analysis(claim, matches, start, original_url)
            else:
                ctx.session.state["scored_result"] = self._generate_fallback_analysis(claim, matches, start, original_url)
                
        except Exception as e:
            print(f"Error in truth scorer analysis: {e}")
            ctx.session.state["scored_result"] = self._generate_fallback_analysis(claim, matches, start, original_url)
            
        yield

    def _generate_fallback_analysis(self, claim: str, matches: list, start_time: float, original_url: str = "") -> dict:
        """Genera análisis fallback más profesional cuando el LLM falla"""
        import time
        from urllib.parse import urlparse
        
        processing_time = round(time.time() - start_time, 2)
        
        # Evaluar credibilidad de la fuente original
        source_credibility = self._evaluate_source_credibility(original_url)
        base_credibility_score = source_credibility["base_score"]
        
        if matches:
            # Analizar las coincidencias para determinar score específico
            num_matches = len(matches)
            
            # Analizar veredictos específicos de fact-checkers
            verdicts = []
            sources = []
            for match in matches:
                rating = match.get("rating", match.get("verdict", match.get("fact_check_result", "")))
                if rating:
                    verdicts.append(rating.lower())
                source = match.get("source", match.get("url", ""))
                if source:
                    sources.append(source)
            
            # Determinar score basado en veredictos específicos
            false_indicators = ["false", "falso", "incorrect", "debunked", "misleading"]
            true_indicators = ["true", "verdadero", "correct", "accurate", "verified"]
            mixed_indicators = ["mixed", "partly", "context", "needs context"]
            
            false_count = sum(1 for v in verdicts if any(fi in v for fi in false_indicators))
            true_count = sum(1 for v in verdicts if any(ti in v for ti in true_indicators))
            mixed_count = sum(1 for v in verdicts if any(mi in v for mi in mixed_indicators))
            
            # Ajustar score considerando credibilidad de fuente original
            base_credibility_score = source_credibility["base_score"]
            
            if true_count > false_count and true_count > mixed_count:
                score = min(5, base_credibility_score + 1)
                label = "Mostly True"
                analysis = f"The claim from {source_credibility['label']} source shows strong verification support. Analysis of {num_matches} fact-checker source(s) indicates {true_count} sources support the claim with {false_count} contradicting and {mixed_count} requiring additional context."
                confidence = 85
            elif false_count > true_count and false_count > mixed_count:
                # Fuentes confiables con contradicciones directas requieren análisis cuidadoso
                if base_credibility_score >= 4:
                    score = 2  # No tan bajo para fuentes muy confiables
                    label = "Needs Context"
                    analysis = f"Despite the {source_credibility['label']} source, {false_count} fact-checkers contradict this claim. This suggests the information may need additional context or verification, though the original source remains generally reliable."
                else:
                    score = 1
                    label = "Mostly False"
                    analysis = f"Analysis of {num_matches} fact-checker source(s) indicates significant issues with this claim. {false_count} sources contradict it with {true_count} supporting and {mixed_count} requiring context."
                confidence = 80
            elif mixed_count > 0 or (true_count == false_count and true_count > 0):
                score = max(3, base_credibility_score)
                label = "Context Needed"
                analysis = f"The claim from {source_credibility['label']} source shows mixed verification results from {num_matches} fact-checker sources. {true_count} sources support, {false_count} contradict, and {mixed_count} indicate additional context is needed."
                confidence = 70
            else:
                # Sin veredictos claros pero hay coincidencias
                score = max(3, base_credibility_score)
                label = "Unclear"
                analysis = f"Found {num_matches} related fact-check sources but verifications are inconclusive. The {source_credibility['label']} original source suggests basic reliability, but specific claim verification remains unclear."
                confidence = 60
        else:
            # Sin coincidencias - considerar solo credibilidad de fuente
            score = base_credibility_score
            if base_credibility_score >= 4:
                label = "Likely Accurate"
                analysis = f"No direct fact-check coverage found for this specific claim, but it originates from a {source_credibility['label']} source ({source_credibility['domain']}). The absence of contradictory fact-checks combined with the source's established credibility suggests basic reliability."
                confidence = 75
            elif base_credibility_score >= 3:
                label = "Likely Accurate"
                analysis = f"No specific fact-check verification found, but the claim comes from a {source_credibility['label']} source. While not independently verified, the source's general reliability provides reasonable confidence."
                confidence = 65
            else:
                label = "Unverified"
                analysis = f"No matching fact-check sources found and the original source credibility is {source_credibility['label']}. Independent verification is recommended before accepting this claim."
                confidence = 40

        return {
            "score": score,
            "label": label,
            "main_claim": claim,
            "detailed_analysis": analysis,
            "verified_sources": [m.get("url", "") for m in matches if m.get("url")],
            "match_type": "derivative" if matches else "tangential",
            "recommendation": f"For claims from {source_credibility['label']} sources: {self._get_recommendation_by_credibility(source_credibility['tier'], bool(matches))}",
            "media_literacy_tip": f"When evaluating {source_credibility['label']} sources: {self._get_media_tip_by_credibility(source_credibility['tier'])}",
            "confidence_level": confidence,
            "processing_time": processing_time
        }

    def _evaluate_source_credibility(self, url: str) -> dict:
        """Evalúa la credibilidad de una fuente basada en su dominio"""
        from urllib.parse import urlparse
        
        if not url:
            return {"tier": 4, "label": "Unknown", "domain": "unknown", "base_score": 2}
        
        try:
            domain = urlparse(url).netloc.lower()
        except:
            return {"tier": 4, "label": "Unknown", "domain": "unknown", "base_score": 2}
        
        # Tier 1: Muy confiables (score base 4)
        tier1_domains = [
            "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", 
            "npr.org", "pbs.org", "pbs.com"
        ]
        
        # Tier 2: Confiables (score base 3-4)
        tier2_domains = [
            "theguardian.com", "nytimes.com", "washingtonpost.com", 
            "cnn.com", "abcnews.go.com", "cbsnews.com", "nbcnews.com",
            "wsj.com", "bloomberg.com", "time.com", "economist.com"
        ]
        
        # Tier 3: Moderadamente confiables (score base 3)
        tier3_domains = [
            "usatoday.com", "latimes.com", "newsweek.com", 
            "politico.com", "axios.com", "thehill.com"
        ]
        
        if any(d in domain for d in tier1_domains):
            return {"tier": 1, "label": "Highly Trusted", "domain": domain, "base_score": 4}
        elif any(d in domain for d in tier2_domains):
            return {"tier": 2, "label": "Trusted", "domain": domain, "base_score": 4}
        elif any(d in domain for d in tier3_domains):
            return {"tier": 3, "label": "Generally Reliable", "domain": domain, "base_score": 3}
        else:
            return {"tier": 4, "label": "Unknown Credibility", "domain": domain, "base_score": 2}
    
    def _get_recommendation_by_credibility(self, tier: int, has_matches: bool) -> str:
        """Genera recomendación basada en tier de credibilidad"""
        if tier == 1:
            return "Cross-reference with other Tier 1 sources for confirmation" if not has_matches else "Review fact-check details for any specific concerns"
        elif tier == 2:
            return "Verify with additional reputable sources" if not has_matches else "Consider fact-check findings in context of source reputation"
        elif tier == 3:
            return "Seek confirmation from higher-tier sources" if not has_matches else "Prioritize fact-check findings over original source"
        else:
            return "Verify through multiple independent, established news sources" if not has_matches else "Rely primarily on fact-check findings"
    
    def _get_media_tip_by_credibility(self, tier: int) -> str:
        """Genera tip de media literacy basado en tier"""
        if tier == 1:
            return "Even highly trusted sources can have errors; look for corrections and updates"
        elif tier == 2:
            return "Generally reliable but always cross-reference significant claims"
        elif tier == 3:
            return "Verify important claims with multiple sources before sharing"
        else:
            return "Unknown sources require extra verification from established outlets"
