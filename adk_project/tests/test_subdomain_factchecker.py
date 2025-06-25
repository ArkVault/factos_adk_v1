import sys
import os
sys.path.insert(0, '/Users/gibrann/Documents/factos_agents')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import pytest
import asyncio
from urllib.parse import urlparse

from adk_project.agents.fact_check_matcher_agent import factchecker_scraper

@pytest.mark.asyncio
async def test_subdomain_filtering():
    # Simula un HTML con enlaces a subdominios y dominios principales
    html = '''
    <html><body>
    <a href="/url?q=https://es.snopes.com/fact-check/foo&sa=U">ES Snopes</a>
    <a href="/url?q=https://www.snopes.com/fact-check/bar&sa=U">WWW Snopes</a>
    <a href="/url?q=https://snopes.com/fact-check/baz&sa=U">Root Snopes</a>
    <a href="/url?q=https://not-snopes.com/fact-check/bad&sa=U">Not Snopes</a>
    </body></html>
    '''
    # Monkeypatch fetch_url para devolver el HTML simulado
    async def fake_fetch_url(session, url):
        return html
    # Parchea la función fetch_url
    factchecker_scraper.fetch_url = fake_fetch_url
    # Ejecuta la búsqueda
    async with asyncio.Semaphore(1):
        session = None  # No se usa en fake_fetch_url
        links = await factchecker_scraper.search_factchecker(session, "https://www.snopes.com/", "test")
    # Debe aceptar todos los subdominios válidos y el dominio raíz, pero no dominios externos
    assert any("es.snopes.com" in l for l in links)
    assert any("www.snopes.com" in l for l in links)
    assert any("snopes.com/fact-check/baz" in l for l in links)
    assert not any("not-snopes.com" in l for l in links)
    print("Links filtrados:", links)
