"""
RootAgent (Orquestador principal)
Orquesta el flujo secuencial de los agentes del sistema de verificación de noticias.
"""

from google.adk.agents import SequentialAgent
from adk_project.agents.smart_scraper_agent import SmartScraperAgent
from adk_project.agents.claim_extractor_agent import ClaimExtractorAgent
from adk_project.agents.fact_check_matcher_agent import FactCheckMatcherAgent
from adk_project.agents.truth_scorer_agent import TruthScorerAgent
from adk_project.agents.response_formatter_agent import ResponseFormatterAgent

class RootAgent(SequentialAgent):
    def __init__(self):
        super().__init__(
            name="RootAgent",
            description="Orquesta el flujo de verificación de noticias usando agentes especializados.",
            sub_agents=[
                SmartScraperAgent(),
                ClaimExtractorAgent(),
                FactCheckMatcherAgent(),
                TruthScorerAgent(),
                ResponseFormatterAgent()
            ]
        )

root_agent = RootAgent() 