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

        # Construir prompt para análisis profesional
        analysis_prompt = f"""
        Como experto verificador de hechos, analiza la veracidad de una afirmación basándote en las verificaciones encontradas en fact-checkers profesionales y medios verificados.

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
        
        CRITERIOS DE PUNTUACIÓN (0-5):
        - Si hay fact-checkers que verificaron directamente: usar sus veredictos como base principal
        - Si solo hay medios verificados: evaluar si confirman, contradicen o proporcionan contexto
        - Si no hay fuentes: puntuar basado en ausencia de verificación profesional
        
        FORMATO DE RESPUESTA REQUERIDO (JSON válido):
        {{
            "score": [número 0-5],
            "label": "[etiqueta descriptiva]",
            "main_claim": "{claim}",
            "detailed_analysis": "[análisis profesional de 2-3 oraciones explicando tu puntuación basada en la evidencia encontrada, mencionando específicamente el tipo y calidad de fuentes]",
            "verified_sources": [lista de URLs SOLO de fuentes que tienen similitud real con la afirmación],
            "match_type": "[direct/derivative/tangential - determina el tipo de coincidencia: direct=fuentes abordan exactamente la afirmación, derivative=abordan aspectos relacionados, tangential=temas relacionados pero no directos]",
            "recommendation": "[recomendación específica basada en el análisis y tipo de fuentes]",
            "media_literacy_tip": "[consejo específico para este tipo de afirmación y fuentes disponibles]",
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
                    ctx.session.state["scored_result"] = self._generate_fallback_analysis(claim, matches, start)
            else:
                ctx.session.state["scored_result"] = self._generate_fallback_analysis(claim, matches, start)
                
        except Exception as e:
            print(f"Error in truth scorer analysis: {e}")
            ctx.session.state["scored_result"] = self._generate_fallback_analysis(claim, matches, start)
            
        yield

    def _generate_fallback_analysis(self, claim: str, matches: list, start_time: float) -> dict:
        """Genera análisis fallback más profesional cuando el LLM falla"""
        import time
        processing_time = round(time.time() - start_time, 2)
        
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
            
            if true_count > false_count and true_count > mixed_count:
                score = 4
                label = "Mostly True"
                analysis = f"Analysis of {num_matches} fact-checker source(s) shows predominant verification as accurate. {true_count} sources support the claim with {false_count} contradicting and {mixed_count} requiring additional context."
                confidence = 80
            elif false_count > true_count and false_count > mixed_count:
                score = 1
                label = "Mostly False"
                analysis = f"Analysis of {num_matches} fact-checker source(s) indicates the claim is predominantly inaccurate. {false_count} sources contradict the claim with {true_count} supporting and {mixed_count} requiring context."
                confidence = 85
            elif mixed_count > 0 or (true_count == false_count and true_count > 0):
                score = 3
                label = "Context Needed"
                analysis = f"Analysis of {num_matches} fact-checker source(s) shows mixed verification results. {true_count} sources support, {false_count} contradict, and {mixed_count} indicate additional context is needed."
                confidence = 70
            elif num_matches >= 3:
                score = 2
                label = "Unclear"
                analysis = f"Found {num_matches} related fact-check sources but verifications are inconclusive. Multiple sources cover related topics but don't provide clear consensus on this specific claim."
                confidence = 60
            else:
                score = 2
                label = "Limited Coverage"
                analysis = f"Found {num_matches} related fact-check source(s) with limited direct verification. Available coverage suggests relevance but requires additional independent verification."
                confidence = 55
        else:
            score = 1
            label = "Unverified"
            analysis = "No matching fact-check sources found in professional verification databases. The absence of coverage doesn't confirm or deny the claim but indicates it hasn't been independently verified by major fact-checking organizations."
            confidence = 40

        return {
            "score": score,
            "label": label,
            "main_claim": claim,
            "detailed_analysis": analysis,
            "verified_sources": [m.get("url", "") for m in matches if m.get("url")],
            "match_type": "derivative" if matches else "tangential",
            "recommendation": f"Seek verification from primary sources and additional independent outlets. Analysis confidence: {confidence}%",
            "media_literacy_tip": "Cross-reference claims with multiple fact-checking organizations and look for consensus among reputable sources.",
            "confidence_level": confidence,
            "processing_time": processing_time
        }
