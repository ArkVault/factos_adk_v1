import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict
import hashlib
import time
import os
from fuzzywuzzy import fuzz
import urllib.parse
from urllib.parse import urlparse
from adk_project.utils.firecrawl import firecrawl_search_tool, firecrawl_crawl_and_match

FACTCHECKERS = [
    "https://www.factcheck.org/",
    "https://reporterslab.org/fact-checking/",
    "https://apnews.com/ap-fact-check",
    "https://www.snopes.com/",
    "https://www.politifact.com/",
    "https://fullfact.org/",
    "https://factuel.afp.com/",
    "https://www.reuters.com/fact-check",  # Reuters Fact Check añadido
    "https://www.washingtonpost.com/politics/fact-checker/",  # Washington Post Fact Checker añadido
    "https://factcheckni.org/",
    "https://factcheck.kz/",
    "https://www.factcrescendo.com/",
    "https://www.bbc.com/news/bbcverify"  # BBC Verify añadido
]

CACHE: Dict[str, Dict] = {}
CACHE_TTL = 3600  # 1 hora

def cache_key(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()

async def get_factchecker_claims(main_claim: str) -> List[Dict]:
    print(f"[get_factchecker_claims] Buscando claim: {main_claim}")
    key = cache_key(main_claim)
    now = time.time()
    if key in CACHE and now - CACHE[key]["ts"] < CACHE_TTL:
        print("[get_factchecker_claims] Usando cache")
        return CACHE[key]["data"]
    domains = [urlparse(fc).netloc for fc in FACTCHECKERS]
    # 1. Hacer webcrawling en todos los fact-checkers para detectar subdominios/páginas con alta similitud
    crawl_candidates = await firecrawl_crawl_and_match(main_claim, domains, similarity_threshold=70, max_depth=2, limit=10)
    # 2. Filtrar solo los fact-checkers que tengan al menos una página/subdominio con alta similitud
    relevant_domains = list(set(urlparse(page.get("url", "")).netloc for page in crawl_candidates))
    print(f"[get_factchecker_claims] Fact-checkers relevantes por similitud: {relevant_domains}")
    print(f"[get_factchecker_claims] Páginas candidatas por crawling:")
    for page in crawl_candidates:
        print(f"  - url: {page.get('url')} | title: {page.get('title')} | sim_title: {page.get('similarity_title', 0)} | sim_subdomain: {page.get('similarity_subdomain', 0)}")
    claims = []
    # 3. Solo en esos fact-checkers hacer el scraping/análisis profundo (search + crawling)
    if relevant_domains:
        firecrawl_results = await firecrawl_search_tool(main_claim, relevant_domains, limit=7, include_subdomains=True, similarity_threshold=70)
        if firecrawl_results and firecrawl_results.get("results"):
            for res in firecrawl_results["results"]:
                headline = res.get("title") or res.get("markdown", "").split('\n')[0] or ""
                main_claim_text = res.get("markdown") or res.get("html") or res.get("rawHtml") or ""
                claims.append({
                    "headline": headline,
                    "main_claim": main_claim_text[:500],
                    "url": res.get("url", ""),
                    "score": res.get("similarity", 0),
                    "report": f"Similitud de encabezado: {res.get('similarity', 0)}"
                })
    # Añadir también los matches directos del crawling inicial
    for page in crawl_candidates:
        headline = page.get("title") or page.get("markdown", "").split('\n')[0] or ""
        main_claim_text = page.get("markdown") or page.get("html") or page.get("rawHtml") or ""
        claims.append({
            "headline": headline,
            "main_claim": main_claim_text[:500],
            "url": page.get("url", ""),
            "score": max(page.get("similarity_title", 0), page.get("similarity_subdomain", 0)),
            "report": f"Similitud por crawling: title={page.get('similarity_title', 0)}, subdomain={page.get('similarity_subdomain', 0)}"
        })
    print(f"[get_factchecker_claims] Claims finales encontrados:")
    for claim in claims:
        print(f"  - url: {claim['url']} | headline: {claim['headline']} | score: {claim['score']}")
    CACHE[key] = {"data": claims, "ts": now}
    return claims

# Ejemplo de uso:
# claims = asyncio.run(get_factchecker_claims("Coffee prevents cancer"))
# print(claims)
