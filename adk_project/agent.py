"""
RootAgent (Orquestador principal)
Orquesta el flujo secuencial de los agentes del sistema de verificación de noticias.
"""

from google.adk.agents import SequentialAgent
from adk_project.agents.smart_scraper_agent.smart_scraper_agent import SmartScraperAgent
from adk_project.agents.claim_extractor_agent.claim_extractor_agent import ClaimExtractorAgent
from adk_project.agents.fact_check_matcher_agent.fact_check_matcher_agent import FactCheckMatcherAgent
from adk_project.agents.truth_scorer_agent.truth_scorer_agent import TruthScorerAgent
from adk_project.agents.response_formatter_agent.response_formatter_agent import ResponseFormatterAgent

# This is the object that will be passed to the deployment function.
root_agent = SequentialAgent(
    name="FactosAgent",
    sub_agents=[
        SmartScraperAgent(),
        ClaimExtractorAgent(),
        FactCheckMatcherAgent(),
        TruthScorerAgent(),
        ResponseFormatterAgent()
    ]
) 