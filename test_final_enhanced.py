#!/usr/bin/env python3
"""
Final test of the enhanced fact-checking system with:
1. Enhanced semantic webcrawling of fact-checkers
2. Flexible matching based on key terms and context
3. Numeric scores
4. Brief English responses
"""

import asyncio
import sys
import os
sys.path.append('/Users/gibrann/Documents/factos_agents')

from adk_project.agents.root_agent import RootAgent
from google.adk.sessions import Session, InMemorySessionService
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.run_config import RunConfig

async def test_final_enhanced_system():
    print("🔬 FINAL ENHANCED SYSTEM TEST")
    print("=" * 50)
    print("✅ Enhanced semantic webcrawling")
    print("✅ Flexible matching (key terms + context)")
    print("✅ Numeric scores guaranteed")
    print("✅ Brief English responses")
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
            app_name="factos-agents-final-enhanced-test",
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
        print("🔄 Processing through final enhanced pipeline...")
        
        async for event in agent.run_async(ctx):
            pass  # Process all events
        
        # Check results
        if ctx.session.state.get("agui_response"):
            response_dict = ctx.session.state["agui_response"]
            
            print("✅ FINAL ENHANCED RESULTS")
            print("=" * 40)
            print(f"📰 Headline: {response_dict.get('headline', 'N/A')}")
            
            # Verify numeric score
            score = response_dict.get('score', 0)
            score_type = type(score).__name__
            print(f"🎯 Score: {score}/5 (Type: {score_type}) • {response_dict.get('score_label', 'N/A')}")
            
            print(f"📝 Main Claim: {response_dict.get('main_claim', 'N/A')[:100]}...")
            print()
            print("🔍 ENHANCED ANALYSIS:")
            print(f"   {response_dict.get('detailed_analysis', 'N/A')}")
            print()
            print("🎓 CONTEXTUAL MEDIA LITERACY:")
            print(f"   {response_dict.get('media_literacy_tip', 'N/A')}")
            print()
            
            # Enhanced search info
            match_results = ctx.session.state.get("match_results", {})
            search_method = match_results.get("search_method", "standard")
            verified_sources = response_dict.get('verified_sources', [])
            
            print("📊 ENHANCED SEARCH DETAILS:")
            print(f"   Method: {search_method}")
            print(f"   Sources found: {len(verified_sources)}")
            print(f"   Fact-checkers processed: {len(match_results.get('matches', []))}")
            print()
            
            # Quality metrics
            analysis = response_dict.get('detailed_analysis', '')
            literacy = response_dict.get('media_literacy_tip', '')
            analysis_words = len(analysis.split())
            literacy_words = len(literacy.split())
            
            print("📏 FINAL QUALITY METRICS:")
            print(f"   Score is numeric: {'✅ Yes' if isinstance(score, (int, float)) else '❌ No'}")
            print(f"   Analysis length: {analysis_words} words ({'✅ Brief' if analysis_words <= 50 else '⚠️ Long'})")
            print(f"   Literacy tip length: {literacy_words} words ({'✅ Brief' if literacy_words <= 50 else '⚠️ Long'})")
            print(f"   Language: {'✅ English' if 'the' in analysis.lower() else '⚠️ Spanish detected'}")
            print(f"   Mentions fact-checks: {'✅ Yes' if 'fact' in analysis.lower() else '⚠️ No'}")
            print(f"   Contextual advice: {'✅ Yes' if 'verify' in literacy.lower() or 'check' in literacy.lower() else '⚠️ Generic'}")
            
            print()
            print("🎉 FINAL ASSESSMENT:")
            all_checks = [
                isinstance(score, (int, float)),
                analysis_words <= 50,
                'the' in analysis.lower(),
                'fact' in analysis.lower(),
                search_method in ['webcrawling + firecrawl + perplexity', 'webcrawling + firecrawl', 'webcrawling']
            ]
            
            passed = sum(all_checks)
            total = len(all_checks)
            
            print(f"   Quality Score: {passed}/{total} checks passed")
            if passed == total:
                print("   🏆 EXCELLENT: All requirements met!")
            elif passed >= total - 1:
                print("   🥈 GOOD: Almost all requirements met")
            else:
                print("   🔧 NEEDS IMPROVEMENT: Some requirements not met")
            
        else:
            print("❌ No agui_response found in session state")
            print("Available keys:", list(ctx.session.state.keys()))
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_final_enhanced_system())
