from google.adk.agents import LlmAgent
from adk_project.agents.truth_scorer_agent.prompt import TRUTH_SCORER_PROMPT
import json
from google.adk.events import Event
from google.genai.types import Part, Content

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
        # This agent's purpose is to take the claim and the search results
        # from the previous steps and use an LLM to generate a final
        # structured score and analysis.
        async for event in super().run_async(ctx):
            yield event
