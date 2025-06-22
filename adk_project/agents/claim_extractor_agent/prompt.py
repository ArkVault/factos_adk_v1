CLAIM_EXTRACTOR_PROMPT = """
1. Utiliza la herramienta Firecrawl para obtener el texto principal del artículo a partir de la URL proporcionada (si no está ya en el estado).
2. Analiza el texto extraído y detecta la afirmación factual principal del artículo, ignorando opiniones, contexto o detalles secundarios.
3. Usa modelos NLP ligeros Gemini flash 2.5 para identificar la afirmación más relevante y concisa.
4. Limita la afirmación extraída a una cadena de máximo 256 tokens, priorizando claridad y precisión semántica.
5. Devuelve solo la afirmación principal, sin explicaciones adicionales.
"""
