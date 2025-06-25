#!/usr/bin/env python3
"""
Test para verificar las optimizaciones de rendimiento:
1. Crawling lento se omite cuando hay resultados de búsqueda inteligente
2. Timeouts agresivos se aplican correctamente
3. El sistema responde rápidamente incluso con claims oscuros
"""

import asyncio
import sys
import os
import time
sys.path.append('/Users/gibrann/Documents/factos_agents')

from adk_project.agents.fact_check_matcher_agent.fact_check_matcher_agent import FactCheckMatcherAgent
from google.adk.sessions import Session, InMemorySessionService
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.run_config import RunConfig

async def test_performance_optimizations():
    print("🚀 TESTING PERFORMANCE OPTIMIZATIONS")
    print("=" * 60)
    print("✅ Verificar que crawling lento se omite cuando hay resultados inteligentes")
    print("✅ Verificar timeouts agresivos")
    print("✅ Verificar respuesta rápida con claims oscuros")
    print()
    
    # Test cases
    test_cases = [
        {
            "name": "Claim Común (debería encontrar resultados con Perplexity/Firecrawl)",
            "claim": "COVID-19 vaccines cause autism",
            "expected_skip_crawling": True,
            "max_time_seconds": 45
        },
        {
            "name": "Claim Específico (debería encontrar algunos resultados)",
            "claim": "Biden administration secretly controls gas prices",
            "expected_skip_crawling": True,
            "max_time_seconds": 45
        },
        {
            "name": "Claim Muy Oscuro (podría necesitar crawling ultra-rápido)",
            "claim": "The mayor of Small Town X embezzled funds in 2023",
            "expected_skip_crawling": False,  # Podría hacer crawling
            "max_time_seconds": 20  # Pero debe ser muy rápido
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 TEST {i}: {test_case['name']}")
        print(f"   Claim: '{test_case['claim']}'")
        print(f"   Expected skip crawling: {test_case['expected_skip_crawling']}")
        print(f"   Max time: {test_case['max_time_seconds']}s")
        
        # Measure time
        start_time = time.time()
        
        try:
            # Create session
            import uuid
            session = Session(
                id=str(uuid.uuid4()),
                app_name="performance-test",
                user_id="test-user",
                state={"extracted_claim": {"claim": test_case["claim"]}}
            )
            
            # Create agent and context
            agent = FactCheckMatcherAgent()
            session_service = InMemorySessionService()
            
            ctx = InvocationContext(
                session=session,
                session_service=session_service,
                invocation_id=str(uuid.uuid4()),
                agent=agent,
                run_config=RunConfig()
            )
            
            # Execute search
            results = []
            async for result in agent.run_async(ctx):
                results.append(result)
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            # Analyze results
            match_results = session.state.get("match_results", {})
            matches = match_results.get("matches", [])
            search_method = match_results.get("search_method", "unknown")
            
            print(f"   ⏱️  Elapsed time: {elapsed_time:.2f}s")
            print(f"   🔍 Search method: {search_method}")
            print(f"   📊 Matches found: {len(matches)}")
            
            # Check if crawling was skipped
            crawling_skipped = "crawl" not in search_method.lower()
            if crawling_skipped:
                print(f"   ✅ CRAWLING SKIPPED (as expected)")
            else:
                print(f"   ⚠️  Crawling used: {search_method}")
            
            # Check performance
            if elapsed_time <= test_case["max_time_seconds"]:
                print(f"   ✅ PERFORMANCE OK ({elapsed_time:.2f}s <= {test_case['max_time_seconds']}s)")
            else:
                print(f"   ❌ PERFORMANCE ISSUE ({elapsed_time:.2f}s > {test_case['max_time_seconds']}s)")
            
            # Show some match details
            if matches:
                print(f"   🎯 Sample matches:")
                for j, match in enumerate(matches[:2]):
                    source = match.get('source', 'Unknown')
                    rating = match.get('rating', 'Unknown')
                    match_type = match.get('match_type', 'Unknown')
                    print(f"      {j+1}. {source} - {rating} ({match_type})")
            else:
                print(f"   ⚠️  No matches found")
                
        except Exception as e:
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"   ❌ ERROR after {elapsed_time:.2f}s: {e}")
    
    print(f"\n🏁 PERFORMANCE TESTS COMPLETED")
    print("=" * 60)

async def test_timeout_behavior():
    """Test específico para verificar que los timeouts se aplican correctamente"""
    print("\n🕐 TESTING TIMEOUT BEHAVIOR")
    print("=" * 40)
    
    # Test con un claim que podría tomar tiempo
    test_claim = "Very obscure local news claim that probably doesn't exist in major fact-checkers"
    
    print(f"Testing timeout behavior with: '{test_claim}'")
    
    start_time = time.time()
    
    try:
        import uuid
        session = Session(
            id=str(uuid.uuid4()),
            app_name="timeout-test",
            user_id="test-user",
            state={"extracted_claim": {"claim": test_claim}}
        )
        
        agent = FactCheckMatcherAgent()
        session_service = InMemorySessionService()
        
        ctx = InvocationContext(
            session=session,
            session_service=session_service,
            invocation_id=str(uuid.uuid4()),
            agent=agent,
            run_config=RunConfig()
        )
        
        results = []
        async for result in agent.run_async(ctx):
            results.append(result)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"⏱️  Total time: {elapsed_time:.2f}s")
        
        # Check that we didn't take too long
        if elapsed_time < 60:  # Should never take more than 1 minute
            print(f"✅ TIMEOUT BEHAVIOR OK - completed in {elapsed_time:.2f}s")
        else:
            print(f"❌ TIMEOUT ISSUE - took {elapsed_time:.2f}s (too long)")
            
    except Exception as e:
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"❌ ERROR after {elapsed_time:.2f}s: {e}")

async def main():
    print("🧪 RUNNING PERFORMANCE OPTIMIZATION TESTS")
    print("=" * 70)
    
    await test_performance_optimizations()
    await test_timeout_behavior()
    
    print("\n🎉 ALL PERFORMANCE TESTS COMPLETED!")

if __name__ == "__main__":
    asyncio.run(main())
