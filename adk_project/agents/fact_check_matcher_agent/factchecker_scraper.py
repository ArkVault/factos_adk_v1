import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict
import hashlib
import time
from urllib.parse import quote_plus

# We will only use fact-checkers that have a searchable interface.
FACTCHECKERS = {
    "factcheck.org": "https://www.factcheck.org/?s={query}",
    "apnews.com": "https://apnews.com/search?q={query}"
}

CACHE: Dict[str, Dict] = {}
CACHE_TTL = 3600  # 1 hora

async def fetch_url(session, url):
    # Using a realistic user-agent to avoid being blocked.
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        async with session.get(url, timeout=10, headers=headers) as resp:
            if resp.status == 200:
                return await resp.text()
            return None
    except Exception:
        return None

async def parse_factcheck_org(html: str) -> List[Dict]:
    """Parses the search results from factcheck.org."""
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    articles = soup.find_all('article', limit=3)
    results = []
    for article in articles:
        title_element = article.find('h3')
        link_element = title_element.find('a') if title_element else None
        if title_element and link_element:
            results.append({
                "claim": title_element.text.strip(),
                "source": link_element['href'],
                "confidence": 0.9  # Confidence is hard to gauge, so we use a default
            })
    return results

async def parse_apnews(html: str) -> List[Dict]:
    """Parses the search results from apnews.com."""
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.find_all('div', class_='Card', limit=3)
    results = []
    for card in cards:
        title_element = card.find('h3')
        link_element = card.find('a', class_='Link')
        if title_element and link_element and 'fact-check' in link_element['href']:
             # Construct absolute URL if it's relative
            url = link_element['href']
            if not url.startswith('http'):
                url = f"https://apnews.com{url}"
            results.append({
                "claim": title_element.text.strip(),
                "source": url,
                "confidence": 0.9
            })
    return results

async def search_and_parse(session, site: str, search_url: str, query: str) -> List[Dict]:
    """Fetches and parses results for a single fact-checker."""
    url = search_url.format(query=quote_plus(query))
    html = await fetch_url(session, url)
    if site == "factcheck.org":
        return await parse_factcheck_org(html)
    elif site == "apnews.com":
        return await parse_apnews(html)
    return []


def cache_key(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()

async def get_factchecker_claims(main_claim: str) -> List[Dict]:
    key = cache_key(main_claim)
    now = time.time()
    if key in CACHE and now - CACHE[key]["ts"] < CACHE_TTL:
        print("--- Returning cached fact-check results ---")
        return CACHE[key]["data"]

    print(f"--- Performing live fact-check for: '{main_claim}' ---")
    async with aiohttp.ClientSession() as session:
        tasks = [search_and_parse(session, site, url, main_claim) for site, url in FACTCHECKERS.items()]
        results_list = await asyncio.gather(*tasks)
        
        # Flatten the list of lists into a single list
        all_claims = [claim for sublist in results_list for claim in sublist]
        
        CACHE[key] = {"data": all_claims, "ts": now}
        return all_claims

# Ejemplo de uso:
# claims = asyncio.run(get_factchecker_claims("Coffee prevents cancer"))
# print(claims)
