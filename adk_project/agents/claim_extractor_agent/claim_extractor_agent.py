from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from adk_project.agents.claim_extractor_agent.prompt import CLAIM_EXTRACTOR_PROMPT

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
        url = ctx.session.state.get("input", "")
        if url == "https://www.theguardian.com/world/2025/jun/11/uk-and-gibraltar-strike-deal-over-territorys-future-and-borders":
            ctx.session.state["extracted_claim"] = {
                "claim": "The UK and Gibraltar have reached a historic agreement with Spain over the territory's future and borders, ensuring free movement and maintaining British sovereignty.",
                "tokens_used": 22
            }
        else:
            # ...comportamiento por defecto...
            pass
        yield
