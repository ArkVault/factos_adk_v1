TRUTH_SCORER_PROMPT = """
1. Recibe la afirmación y las coincidencias de fact-check encontradas.
2. Asigna un puntaje de desinformación en la escala 0-3:
   - 0: Verificado verdadero
   - 1: Contexto necesario
   - 2: Engañoso
   - 3: Falso
3. Genera una explicación breve y clara del puntaje asignado.
4. Cita explícitamente las fuentes coincidentes utilizadas para la decisión.
5. Si la confianza es baja, evita llamar a LLMs y usa lógica basada en reglas o ejemplos.
"""
