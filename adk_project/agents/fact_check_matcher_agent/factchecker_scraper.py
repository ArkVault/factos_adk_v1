import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict
import hashlib
import time

FACTCHECKERS = [
    "https://www.factcheck.org/",
    "https://reporterslab.org/fact-checking/",
    "https://apnews.com/ap-fact-check"
]

CACHE: Dict[str, Dict] = {}
CACHE_TTL = 3600  # 1 hora

async def fetch_url(session, url):
    try:
        async with session.get(url, timeout=8) as resp:
            if resp.status == 200:
                return await resp.text()
    except Exception:
        return None

async def search_factchecker(session, base_url: str, query: str) -> List[str]:
    # Estrategia: usar Google site search para limitar scraping
    search_url = f"https://www.google.com/search?q=site:{base_url}+{query}"
    html = await fetch_url(session, search_url)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    links = [a['href'] for a in soup.find_all('a', href=True) if base_url in a['href']]
    return links[:3]  # Limita a 3 resultados por fact-checker

async def scrape_claims_from_page(session, url: str) -> Dict:
    html = await fetch_url(session, url)
    if not html:
        return {}
    soup = BeautifulSoup(html, "html.parser")
    # Heurística simple: busca el primer <h1> y el primer <p> largo
    headline = soup.find('h1').get_text(strip=True) if soup.find('h1') else ""
    paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text(strip=True)) > 80]
    main_claim = paragraphs[0] if paragraphs else ""
    return {
        "headline": headline,
        "main_claim": main_claim,
        "url": url
    }

def cache_key(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()

async def get_factchecker_claims(main_claim: str) -> List[Dict]:
    key = cache_key(main_claim)
    now = time.time()
    if key in CACHE and now - CACHE[key]["ts"] < CACHE_TTL:
        return CACHE[key]["data"]
    async with aiohttp.ClientSession() as session:
        tasks = [search_factchecker(session, fc, main_claim) for fc in FACTCHECKERS]
        results = await asyncio.gather(*tasks)
        urls = [url for sublist in results for url in sublist]
        scrape_tasks = [scrape_claims_from_page(session, url) for url in urls]
        claims = await asyncio.gather(*scrape_tasks)
        claims = [c for c in claims if c]
        CACHE[key] = {"data": claims, "ts": now}
        return claims

# Ejemplo de uso:
# claims = asyncio.run(get_factchecker_claims("Coffee prevents cancer"))
# print(claims)
