import sys
import pytest
import asyncio
sys.path.insert(0, '/Users/gibrann/Documents/factos_agents')
from adk_project.agents.fact_check_matcher_agent.factchecker_scraper import search_factchecker
from adk_project.agents.fact_check_matcher_agent.fact_check_matcher_agent import semantic_match_with_gemini

@pytest.mark.asyncio
async def test_factchecker_end_to_end():
    # Claim real extraído de una noticia
    claim = "Russia launched its largest aerial barrage against Ukraine since the war began, targeting Kyiv and other cities."
    # Usamos snopes como ejemplo de fact-checker
    base_url = "https://www.snopes.com/"
    query = "Russia Ukraine aerial barrage"
    # Simula una sesión HTTP (no se usa en fetch_url si se mockea)
    class DummySession:
        pass
    session = DummySession()
    # Monkeypatch fetch_url para devolver HTML simulado con subdominios y dominio raíz
    html = '''
    <html><body>
    <a href="/url?q=https://es.snopes.com/fact-check/foo&sa=U">ES Snopes</a>
    <a href="/url?q=https://www.snopes.com/fact-check/bar&sa=U">WWW Snopes</a>
    <a href="/url?q=https://snopes.com/fact-check/baz&sa=U">Root Snopes</a>
    </body></html>
    '''
    import adk_project.agents.fact_check_matcher_agent.factchecker_scraper as scraper_mod
    async def fake_fetch_url(session, url):
        return html
    scraper_mod.fetch_url = fake_fetch_url
    # Ejecuta el scraping
    links = await search_factchecker(session, base_url, query)
    assert any("es.snopes.com" in l for l in links)
    # Simula claims extraídos de los links
    mock_claims = [
        {"main_claim": "Ukraine was attacked by Russia with a large number of missiles.", "headline": "Massive Russian missile attack on Ukraine", "url": links[0]},
        {"main_claim": "No evidence of a major aerial barrage by Russia.", "headline": "Fact-check: Russian attacks", "url": links[1]}
    ]
    # Ejecuta el matching semántico con Gemini (mockeado para evitar llamada real)
    async def fake_gemini_complete(prompt, model="gemini-2.5-flash"):
        return '{"match_index": 0, "relacion": "equivalente", "explicacion": "Ambos claims se refieren al mismo evento de ataque aéreo masivo."}'
    import adk_project.agents.fact_check_matcher_agent.fact_check_matcher_agent as matcher_mod
    matcher_mod.gemini_complete = fake_gemini_complete
    result = await semantic_match_with_gemini(claim, mock_claims)
    assert result["relation"] == "equivalente"
    assert result["semantic_match"] == mock_claims[0]
    print("End-to-end result:", result)

@pytest.mark.asyncio
async def test_factchecker_end_to_end_real():
    # Claim real extraído de una noticia
    claim = "Russia launched its largest aerial barrage against Ukraine since the war began, targeting Kyiv and other cities."
    # Usamos snopes como ejemplo de fact-checker
    base_url = "https://www.snopes.com/"
    query = "Russia Ukraine aerial barrage"
    import aiohttp
    async with aiohttp.ClientSession() as session:
        links = await search_factchecker(session, base_url, query)
    print("Links encontrados:", links)
    assert links, "No se encontraron links reales de fact-checkers."
    # Simula claims extraídos de los links (en un caso real, deberías scrapear cada link para extraer el claim principal)
    mock_claims = [
        {"main_claim": "Ukraine was attacked by Russia with a large number of missiles.", "headline": "Massive Russian missile attack on Ukraine", "url": links[0]},
        {"main_claim": "No evidence of a major aerial barrage by Russia.", "headline": "Fact-check: Russian attacks", "url": links[1] if len(links) > 1 else links[0]}
    ]
    # Matching semántico real con Gemini
    result = await semantic_match_with_gemini(claim, mock_claims)
    print("Resultado Gemini:", result)
    assert "relation" in result
    assert result["semantic_match"] is not None or result["relation"] is not None
