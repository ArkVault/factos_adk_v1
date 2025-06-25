import sys
import pytest
import asyncio
sys.path.insert(0, '/Users/gibrann/Documents/factos_agents')
from adk_project.agents.fact_check_matcher_agent import factchecker_scraper

@pytest.mark.asyncio
async def test_factchecker_subdomain_general():
    # Simula un HTML con enlaces a subdominios y dominios principales de varios fact-checkers
    html = '''
    <html><body>
    <a href="/url?q=https://es.snopes.com/fact-check/foo&sa=U">ES Snopes</a>
    <a href="/url?q=https://www.politifact.com/fact-check/bar&sa=U">WWW Politifact</a>
    <a href="/url?q=https://factcheck.org/fact-check/baz&sa=U">Root Factcheck</a>
    <a href="/url?q=https://sub.fullfact.org/fact-check/abc&sa=U">Sub Fullfact</a>
    <a href="/url?q=https://notafactchecker.com/fact-check/bad&sa=U">Not a Factchecker</a>
    </body></html>
    '''
    async def fake_fetch_url(session, url):
        return html
    factchecker_scraper.fetch_url = fake_fetch_url
    # Prueba con diferentes fact-checkers
    async with asyncio.Semaphore(1):
        session = None
        links_snopes = await factchecker_scraper.search_factchecker(session, "https://www.snopes.com/", "test")
        links_politifact = await factchecker_scraper.search_factchecker(session, "https://www.politifact.com/", "test")
        links_factcheck = await factchecker_scraper.search_factchecker(session, "https://factcheck.org/", "test")
        links_fullfact = await factchecker_scraper.search_factchecker(session, "https://fullfact.org/", "test")
    # Debe aceptar subdominios y dominio raíz de cada uno, pero no dominios externos
    assert any("es.snopes.com" in l for l in links_snopes)
    assert not any("politifact.com" in l for l in links_snopes)
    assert any("www.politifact.com" in l for l in links_politifact)
    assert not any("snopes.com" in l for l in links_politifact)
    assert any("factcheck.org/fact-check/baz" in l for l in links_factcheck)
    assert any("sub.fullfact.org" in l for l in links_fullfact)
    assert not any("notafactchecker.com" in l for l in links_snopes + links_politifact + links_factcheck + links_fullfact)
    print("Links Snopes:", links_snopes)
    print("Links Politifact:", links_politifact)
    print("Links Factcheck:", links_factcheck)
    print("Links Fullfact:", links_fullfact)
