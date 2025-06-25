#!/usr/bin/env python3
"""
Test script para verificar las mejoras en precisión del fact-checking
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from adk_project.agents.truth_scorer_agent.truth_scorer_agent import TruthScorerAgent
from google.adk.sessions import Session, InMemorySessionService
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.run_config import RunConfig
import uuid

async def test_source_credibility():
    """Test source credibility evaluation"""
    agent = TruthScorerAgent()
    
    # Test URLs from different tiers
    test_urls = [
        ("https://www.reuters.com/world/", "Tier 1 - Reuters"),
        ("https://www.bbc.com/news/", "Tier 1 - BBC"), 
        ("https://www.nytimes.com/section/world", "Tier 2 - NYT"),
        ("https://www.theguardian.com/world", "Tier 2 - Guardian"),
        ("https://www.usatoday.com/news/", "Tier 3 - USA Today"),
        ("https://unknown-source.com/", "Tier 4 - Unknown")
    ]
    
    print("=== TESTING SOURCE CREDIBILITY EVALUATION ===")
    for url, description in test_urls:
        credibility = agent._evaluate_source_credibility(url)
        print(f"{description}")
        print(f"  URL: {url}")
        print(f"  Tier: {credibility['tier']}, Label: {credibility['label']}")
        print(f"  Base Score: {credibility['base_score']}")
        print()

async def test_fallback_analysis():
    """Test improved fallback analysis"""
    agent = TruthScorerAgent()
    
    # Test scenarios
    test_cases = [
        {
            "claim": "Climate change affects global weather patterns",
            "matches": [],
            "url": "https://www.bbc.com/news/science",
            "description": "BBC source, no fact-check matches"
        },
        {
            "claim": "New study shows 90% effectiveness in treatment",
            "matches": [{"rating": "true", "source": "FactCheck.org", "url": "https://factcheck.org/test"}],
            "url": "https://www.reuters.com/health/",
            "description": "Reuters source, with supporting fact-check"
        },
        {
            "claim": "Government announces new policy changes",
            "matches": [],
            "url": "https://unknown-news.com/politics",
            "description": "Unknown source, no matches"
        }
    ]
    
    print("=== TESTING IMPROVED FALLBACK ANALYSIS ===")
    for i, case in enumerate(test_cases):
        print(f"\nTest Case {i+1}: {case['description']}")
        print(f"Claim: {case['claim']}")
        print(f"URL: {case['url']}")
        
        result = agent._generate_fallback_analysis(
            claim=case['claim'],
            matches=case['matches'],
            start_time=0,
            original_url=case['url']
        )
        
        print(f"Score: {result['score']}/5 ({result['label']})")
        print(f"Analysis: {result['detailed_analysis']}")
        print(f"Recommendation: {result['recommendation'][:100]}...")
        print("-" * 80)

if __name__ == "__main__":
    asyncio.run(test_source_credibility())
    asyncio.run(test_fallback_analysis())
