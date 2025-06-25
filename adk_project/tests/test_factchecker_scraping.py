import pytest
import asyncio
import time
import os
from dotenv import load_dotenv
from adk_project.agents.fact_check_matcher_agent.factchecker_scraper import get_factchecker_claims
from adk_project.agents.fact_check_matcher_agent.fact_check_matcher_agent import semantic_match_with_gemini

# Cargar variables de entorno desde .env (raíz del proyecto)
load_dotenv()
# Forzar exportación de GOOGLE_API_KEY si está en .env pero no en os.environ
if not os.environ.get("GOOGLE_API_KEY"):
    import pathlib
    from dotenv import dotenv_values
    env_path = pathlib.Path(__file__).parent.parent.parent / ".env"
    env_vars = dotenv_values(env_path)
    if "GOOGLE_API_KEY" in env_vars:
        os.environ["GOOGLE_API_KEY"] = env_vars["GOOGLE_API_KEY"]

@pytest.mark.asyncio
async def test_factchecker_scraping():
    # Claim real extraído de la noticia de CNN
    claim = "Russia launched its largest aerial barrage against Ukraine since the war began, targeting Kyiv and other cities."
    results = await get_factchecker_claims(claim)
    print("Resultados de scraping de fact-checkers:")
    for r in results:
        print(f"- Headline: {r.get('headline')}")
        print(f"  Main claim: {r.get('main_claim')}")
        print(f"  URL: {r.get('url')}")
        print(f"  Score: {r.get('score')}")
        print(f"  Report: {r.get('report')}")
        time.sleep(1)
    if not results:
        print("No se encontraron matches directos. Probando matching semántico con Gemini...")
        # Simula algunos claims para probar Gemini
        mock_claims = [
            {"main_claim": "Ukraine was attacked by Russia with a large number of missiles.", "headline": "Massive Russian missile attack on Ukraine", "url": "https://example.com/1"},
            {"main_claim": "No evidence of a major aerial barrage by Russia.", "headline": "Fact-check: Russian attacks", "url": "https://example.com/2"}
        ]
        sem_result = await semantic_match_with_gemini(claim, mock_claims)
        print("Resultado semántico Gemini:", sem_result)
    assert isinstance(results, list)
    assert len(results) > 0, "No se encontraron resultados en los fact-checkers"
