#!/usr/bin/env python3
"""
Test the improved fact-checking system with:
1. Brief responses in English
2. Escalated search: webcrawling → firecrawl → perplexity
3. Professional analysis
"""

import asyncio
import sys
import os
sys.path.append('/Users/gibrann/Documents/factos_agents')

from adk_project.agents.root_agent import RootAgent
from google.adk.sessions import Session, InMemorySessionService
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.run_config import RunConfig

async def test_improved_system():
    print("🧪 TESTING IMPROVED SYSTEM")
    print("=" * 50)
    print("✅ Brief responses in English")
    print("✅ Escalated search: webcrawling → firecrawl → perplexity")
    print("✅ Professional analysis")
    print()
    
    # Test URL
    test_url = "https://www.theguardian.com/world/2025/may/21/israeli-troops-fire-warning-shots-25-diplomats-visiting-occupied-west-bank"
    
    print(f"📰 Testing URL: {test_url}")
    print()
    
    try:
        # Create session using proper ADK structure
        import uuid
        
        session = Session(
            id=str(uuid.uuid4()),
            app_name="factos-agents-improved-test",
            user_id="test-user",
            state={"input": test_url}
        )
        
        # Initialize RootAgent
        agent = RootAgent()
        session_service = InMemorySessionService()
        
        # Create proper invocation context
        ctx = InvocationContext(
            session=session,
            session_service=session_service,
            invocation_id=str(uuid.uuid4()),
            agent=agent,
            run_config=RunConfig()
        )
        
        # Process the URL
        print("🔄 Processing through improved pipeline...")
        
        async for event in agent.run_async(ctx):
            pass  # Process all events
        
        # Check results
        if ctx.session.state.get("agui_response"):
            response_dict = ctx.session.state["agui_response"]
            
            print("✅ IMPROVED SYSTEM RESULTS")
            print("=" * 40)
            print(f"📰 Headline: {response_dict.get('headline', 'N/A')}")
            print(f"🎯 Score: {response_dict.get('score', 0)}/5 • {response_dict.get('score_label', 'N/A')}")
            print(f"📝 Main Claim: {response_dict.get('main_claim', 'N/A')[:100]}...")
            print()
            print("🔍 ANALYSIS (Brief & Professional):")
            print(f"   {response_dict.get('detailed_analysis', 'N/A')}")
            print()
            print("🎓 MEDIA LITERACY (Contextual & Brief):")
            print(f"   {response_dict.get('media_literacy_tip', 'N/A')}")
            print()
            print("📊 SEARCH INFO:")
            search_method = ctx.session.state.get("match_results", {}).get("search_method", "standard")
            print(f"   Method: {search_method}")
            verified_sources = response_dict.get('verified_sources', [])
            print(f"   Sources: {len(verified_sources)}")
            print()
            
            # Check language and brevity
            analysis = response_dict.get('detailed_analysis', '')
            literacy = response_dict.get('media_literacy_tip', '')
            analysis_words = len(analysis.split())
            literacy_words = len(literacy.split())
            
            print("📏 QUALITY METRICS:")
            print(f"   Analysis length: {analysis_words} words ({'✅ Brief' if analysis_words <= 50 else '⚠️ Long'})")
            print(f"   Literacy tip length: {literacy_words} words ({'✅ Brief' if literacy_words <= 40 else '⚠️ Long'})")
            print(f"   Language: {'✅ English' if 'the' in analysis.lower() else '⚠️ Spanish detected'}")
            
        else:
            print("❌ No agui_response found in session state")
            print("Available keys:", list(ctx.session.state.keys()))
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_improved_system())
