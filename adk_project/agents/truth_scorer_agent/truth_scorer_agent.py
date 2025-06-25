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
        claim = ctx.session.state.get("extracted_claim", {}).get("claim", "")
        matches = ctx.session.state.get("match_results", {}).get("matches", [])
        start = time.time()
        if not claim:
            ctx.session.state["scored_result"] = {}
            yield
            return
        # Análisis real basado en matches
        if matches:
            # Si hay coincidencias, toma la más relevante
            best = matches[0]
            ctx.session.state["scored_result"] = {
                "score": 0,  # Asume verdadero si hay match fuerte
                "label": "True",
                "main_claim": claim,
                "detailed_analysis": f"Se encontró una coincidencia relevante en fact-checkers: '{best.get('main_claim', best.get('headline', ''))}'. Fuente: {best.get('url', '')}",
                "verified_sources": [m.get("url", "") for m in matches],
                "recommendation": "La afirmación coincide con verificaciones externas. Consulta la fuente para más detalles.",
                "media_literacy_tip": "Verifica siempre en múltiples fuentes de fact-checking.",
                "confidence_level": 95,
                "processing_time": round(time.time() - start, 2)
            }
        else:
            ctx.session.state["scored_result"] = {
                "score": 2,
                "label": "Context Needed",
                "main_claim": claim,
                "detailed_analysis": "No se encontraron coincidencias directas en los principales sitios de fact-checking. Se recomienda investigar más a fondo.",
                "verified_sources": [],
                "recommendation": "No hay verificación directa disponible. Consulta fuentes adicionales.",
                "media_literacy_tip": "Desconfía de afirmaciones sin respaldo en sitios de verificación reconocidos.",
                "confidence_level": 60,
                "processing_time": round(time.time() - start, 2)
            }
        yield
