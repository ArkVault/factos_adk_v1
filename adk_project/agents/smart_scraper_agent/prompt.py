SCRAPER_PROMPT = """
1. Valida que la URL proporcionada sea HTTPS, accesible y pertenezca a un dominio de noticias permitido (usa una whitelist).
2. Si la URL es válida, utiliza Firecrawl para extraer únicamente los siguientes campos del artículo: headline, byline, fecha de publicación y texto principal.
3. Limita la profundidad de scraping a 1-2 niveles y evita extraer contenido irrelevante (publicidad, comentarios, etc.).
4. Si la URL no es válida, responde con un error claro y no intentes extraer contenido.
5. Optimiza para bajo uso de tokens y eficiencia en llamadas a Firecrawl.
"""
