MATCHER_PROMPT = """
1. Toma la afirmación extraída y búscala en la base local de fact-checks pre-embebida (Snopes, FactCheck.org, etc.).
2. Utiliza embeddings y similitud de coseno (ej. Faiss, Chroma) para encontrar coincidencias relevantes.
3. Devuelve una lista de coincidencias con: claim verificado, fuente, y nivel de confianza (score de similitud).
4. No realices llamadas a APIs externas en tiempo real; usa solo la base local actualizada semanalmente.
5. Optimiza para velocidad y bajo uso de recursos.
"""
