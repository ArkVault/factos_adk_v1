import os
import aiohttp
import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

async def firecrawl_scrape_tool(url: str):
    FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY")
    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": True
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.firecrawl.dev/v1/scrape",
            json=payload,
            headers=headers
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                # Si hay markdown, inclúyelo explícitamente
                if "markdown" in data:
                    data["markdown"] = data["markdown"]
                return data
            else:
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, "html.parser")
                    # Mejor heurística: headline de <h1>, texto de <article> o <div> largo, y todos los <p> relevantes
                    headline = soup.title.string if soup.title else "No headline found"
                    h1 = soup.find('h1')
                    if h1 and h1.get_text(strip=True):
                        headline = h1.get_text(strip=True)
                    # Busca el bloque de texto más largo en <article>, si existe
                    article_tag = soup.find('article')
                    if article_tag:
                        full_text = article_tag.get_text(separator=' ', strip=True)
                    else:
                        # Si no hay <article>, concatena todos los <p> largos y <div> con mucho texto
                        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text(strip=True)) > 60]
                        divs = [d.get_text(strip=True) for d in soup.find_all('div') if len(d.get_text(strip=True)) > 200]
                        all_blocks = paragraphs + divs
                        # Elimina duplicados y selecciona los más largos
                        all_blocks = list(dict.fromkeys(all_blocks))
                        all_blocks.sort(key=len, reverse=True)
                        full_text = ' '.join(all_blocks[:5]) if all_blocks else ""
                    return {
                        "success": True,
                        "headline": headline,
                        "url": url,
                        "full_text": full_text[:3000]  # Más contexto para el extractor
                    }
                except Exception as e:
                    return {"success": False, "error": str(e), "url": url}

async def firecrawl_search_tool(query: str, domains: list, limit: int = 5, include_subdomains: bool = True, similarity_threshold: int = 70):
    """
    Realiza búsqueda y scraping en los dominios indicados usando el endpoint /search de Firecrawl.
    Busca también en subdominios si include_subdomains=True.
    Primero compara encabezados (title/markdown) con el claim, y si la similitud es alta, extrae el contenido completo del link.
    """
    FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY")
    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "domains": domains,
        "limit": limit,
        "formats": ["markdown", "html", "rawHtml"],
        "onlyMainContent": True,
        "includeSubdomains": include_subdomains
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.firecrawl.dev/v1/search",
            json=payload,
            headers=headers
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                # Heurística: priorizar resultados cuyo encabezado sea similar al claim
                filtered = []
                for res in data.get("results", []):
                    title = res.get("title") or res.get("markdown", "").split('\n')[0] or ""
                    url = res.get("url", "")
                    sim = fuzz.token_set_ratio(query, title)
                    if sim >= similarity_threshold:
                        # Si la similitud es alta, mantener el resultado y priorizar scraping completo
                        filtered.append({**res, "similarity": sim})
                # Si no hay resultados suficientemente similares, devolver los mejores por score
                if not filtered:
                    filtered = sorted(data.get("results", []), key=lambda r: fuzz.token_set_ratio(query, r.get("title", "")), reverse=True)[:limit]
                return {"results": filtered}
            else:
                return {"success": False, "error": f"Status {resp.status}", "details": await resp.text()}

async def firecrawl_crawl_and_match(query: str, domains: list, similarity_threshold: int = 70, max_depth: int = 2, limit: int = 20):
    """
    Hace webcrawling en los dominios de fact-checkers usando Firecrawl, buscando similitud de nombres de subdominios o encabezados.
    Si la similitud es alta, extrae y retorna el contenido relevante.
    """
    from fuzzywuzzy import fuzz
    FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY")
    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }
    results = []
    async with aiohttp.ClientSession() as session:
        for domain in domains:
            payload = {
                "url": f"https://{domain}",
                "maxDepth": max_depth,
                "limit": limit,
                "formats": ["markdown", "html", "rawHtml"],
                "onlyMainContent": True,
                "includeSubdomains": True
            }
            async with session.post(
                "https://api.firecrawl.dev/v1/crawl",
                json=payload,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for page in data.get("results", []):
                        # Similitud por subdominio o encabezado
                        url = page.get("url", "")
                        title = page.get("title") or page.get("markdown", "").split('\n')[0] or ""
                        subdomain = url.split("//")[-1].split("/")[0]
                        sim_title = fuzz.token_set_ratio(query, title)
                        sim_subdomain = fuzz.token_set_ratio(query, subdomain)
                        if sim_title >= similarity_threshold or sim_subdomain >= similarity_threshold:
                            results.append({
                                **page,
                                "similarity_title": sim_title,
                                "similarity_subdomain": sim_subdomain
                            })
    return results
