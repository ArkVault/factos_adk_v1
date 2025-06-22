from google.adk.agents import LlmAgent
from adk_project.agents.response_formatter_agent.prompt import FORMATTER_PROMPT
import asyncio

AGUI_RESPONSE_SCHEMA = {
    "headline": "str",
    "url": "str",
    "score": "int (0-3)",
    "score_label": "str (e.g. 'False', 'True', 'Misleading', 'Context Needed')",
    "main_claim": "str",
    "detailed_analysis": "str",
    "verified_sources": "list[str]",
    "recommendation": "str",
    "media_literacy_tip": "str",
    "processing_time": "float",
    "confidence_level": "int",
    "sources_checked": "int",
    "original_source_label": "str",
    "original_source_url": "str",
    "verified_sources_label": "str"
}

class ResponseFormatterAgent(LlmAgent):
    def __init__(self):
        super().__init__(
            name="ResponseFormatterAgent",
            instruction=FORMATTER_PROMPT + "\n\nLa respuesta debe ser un JSON con la siguiente estructura: " + str(AGUI_RESPONSE_SCHEMA) + "\n\nToma los datos de 'scored_result', 'validated_article', 'match_results' y empaquétalos en 'agui_response' para el frontend.",
            description="Formatea el resultado para AG-UI y frontend custom.",
            output_key="agui_response",
            model="gemini-2.5-flash"
        )

    async def run_async(self, ctx):
        # Empaqueta explícitamente los resultados previos en 'agui_response'
        state = ctx.session.state
        scored = state.get('scored_result', {})
        article = state.get('validated_article', {})
        matches = state.get('match_results', {}).get('matches', [])
        agui_response = {
            "headline": article.get("headline", ""),
            "url": article.get("url", ""),
            "score": scored.get("score", None),
            "score_label": scored.get("label", ""),
            "main_claim": scored.get("main_claim", ""),
            "detailed_analysis": scored.get("detailed_analysis", ""),
            "verified_sources": scored.get("verified_sources", []),
            "recommendation": scored.get("recommendation", ""),
            "media_literacy_tip": scored.get("media_literacy_tip", ""),
            "processing_time": scored.get("processing_time", 0.0),
            "confidence_level": scored.get("confidence_level", 0),
            "sources_checked": len(matches),
            "original_source_label": "Medium Risk",  # Simulado
            "original_source_url": article.get("url", ""),
            "verified_sources_label": "High Trust"  # Simulado
        }
        state["agui_response"] = agui_response
        yield  # Para cumplir con la interfaz async
