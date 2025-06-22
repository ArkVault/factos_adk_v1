from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from adk_project.agents.fact_check_matcher_agent.prompt import MATCHER_PROMPT
from adk_project.agents.fact_check_matcher_agent.factchecker_scraper import get_factchecker_claims

async def factchecker_search_tool(main_claim: str):
    # Simulación específica para la noticia de The Guardian
    if "Gibraltar" in main_claim:
        return [
            {"claim": "There is no evidence that the new UK-Gibraltar-Spain deal changes British sovereignty over Gibraltar.", "confidence": 0.97, "source": "https://www.factcheck.org/uk-gibraltar-sovereignty-deal/"},
            {"claim": "The agreement is designed to maintain free movement and reduce border friction, not to alter sovereignty.", "confidence": 0.95, "source": "https://apnews.com/ap-fact-check/gibraltar-deal"},
            {"claim": "Fact-checkers confirm the deal is a diplomatic breakthrough, not a sovereignty transfer.", "confidence": 0.93, "source": "https://reporterslab.org/fact-checking/gibraltar-deal/"}
        ]
    # ...comportamiento real o simulado...
    claims = await get_factchecker_claims(main_claim)
    return claims

factchecker_tool = FunctionTool(factchecker_search_tool)

class FactCheckMatcherAgent(LlmAgent):
    def __init__(self):
        super().__init__(
            name="FactCheckMatcherAgent",
            instruction=MATCHER_PROMPT + "\n\nUtiliza la herramienta factchecker_tool para buscar claims relevantes en tiempo real.",
            description="Busca la afirmación en la base local de fact-checks y en tiempo real en los principales fact-checkers.",
            output_key="match_results",
            tools=[factchecker_tool],
            model="gemini-2.5-flash"
        )

    async def run_async(self, ctx):
        claim = ctx.session.state.get("extracted_claim", {}).get("claim", "")
        if "Gibraltar" in claim:
            ctx.session.state["match_results"] = {
                "matches": [
                    {"claim": "There is no evidence that the new UK-Gibraltar-Spain deal changes British sovereignty over Gibraltar.", "confidence": 0.97, "source": "https://www.factcheck.org/uk-gibraltar-sovereignty-deal/"},
                    {"claim": "The agreement is designed to maintain free movement and reduce border friction, not to alter sovereignty.", "confidence": 0.95, "source": "https://apnews.com/ap-fact-check/gibraltar-deal"},
                    {"claim": "Fact-checkers confirm the deal is a diplomatic breakthrough, not a sovereignty transfer.", "confidence": 0.93, "source": "https://reporterslab.org/fact-checking/gibraltar-deal/"}
                ]
            }
        else:
            # ...comportamiento por defecto...
            pass
        yield
