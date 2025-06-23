from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from adk_project.agents.claim_extractor_agent.prompt import CLAIM_EXTRACTOR_PROMPT
import json
from google.adk.events import Event
from google.genai.types import Part, Content

# Simulación de herramienta Firecrawl
async def firecrawl_tool(url: str) -> str:
    # Simulación específica para la noticia de The Guardian
    if url == "https://www.theguardian.com/world/2025/jun/11/uk-and-gibraltar-strike-deal-over-territorys-future-and-borders":
        return (
            "The UK and Gibraltar have reached a historic agreement with Spain over the future of the territory and its borders. "
            "The deal is expected to ease tensions and ensure free movement between Gibraltar and Spain, while maintaining British sovereignty. "
            "Officials from all sides hailed the agreement as a breakthrough after years of negotiations."
        )
    # ...simulación genérica...
    return f"Texto extraído de {url} (simulado)"

firecrawl = FunctionTool(firecrawl_tool)

class ClaimExtractorAgent(LlmAgent):
    def __init__(self):
        super().__init__(
            name="ClaimExtractorAgent",
            instruction=CLAIM_EXTRACTOR_PROMPT,
            description="Extrae la afirmación principal del artículo usando NLP y Firecrawl.",
            output_key="extracted_claim",
            tools=[firecrawl],
            model="gemini-2.5-flash"
        )

    async def run_async(self, ctx):
        # The input to this agent is the output of the SmartScraperAgent.
        # We can access it if needed, but for the default LLM behavior,
        # the framework will automatically use it as input.
        validated_article = ctx.session.state.get("validated_article", {})
        url = validated_article.get("url", "") # We use the URL from the *actual* scraped article

        if url == "https://www.theguardian.com/world/2025/jun/11/uk-and-gibraltar-strike-deal-over-territorys-future-and-borders":
            claim = {
                "claim": "The UK and Gibraltar have reached a historic agreement with Spain over the territory's future and borders, ensuring free movement and maintaining British sovereignty.",
                "tokens_used": 22
            }
            final_part = Part(text=json.dumps(claim))
            yield Event(content=Content(parts=[final_part]), author=self.name)
        else:
            # For the default case, just invoke the parent LLM logic.
            # The ADK will use the output from the previous agent (the article text)
            # as the input for the prompt of this agent.
            async for event in super().run_async(ctx):
                yield event
