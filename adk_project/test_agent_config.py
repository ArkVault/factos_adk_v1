"""
Test para verificar la configuración de los agentes y el RootAgent
"""
import pytest
from adk_project.agents.root_agent import RootAgent
from adk_project.agents.smart_scraper_agent import SmartScraperAgent
from adk_project.agents.claim_extractor_agent import ClaimExtractorAgent
from adk_project.agents.fact_check_matcher_agent import FactCheckMatcherAgent
from adk_project.agents.truth_scorer_agent import TruthScorerAgent
from adk_project.agents.response_formatter_agent import ResponseFormatterAgent

def test_root_agent_structure():
    root = RootAgent()
    assert root.name == "RootAgent"
    assert len(root.sub_agents) == 5
    assert isinstance(root.sub_agents[0], SmartScraperAgent)
    assert isinstance(root.sub_agents[1], ClaimExtractorAgent)
    assert isinstance(root.sub_agents[2], FactCheckMatcherAgent)
    assert isinstance(root.sub_agents[3], TruthScorerAgent)
    assert isinstance(root.sub_agents[4], ResponseFormatterAgent)

def test_subagent_prompts():
    root = RootAgent()
    # Verifica que cada agente tenga un prompt no vacío
    for agent in root.sub_agents:
        assert hasattr(agent, 'instruction') and agent.instruction
