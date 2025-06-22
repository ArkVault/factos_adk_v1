FORMATTER_PROMPT = """
1. Recibe el puntaje, explicación y fuentes del agente anterior.
2. Formatea la respuesta en un JSON compacto compatible con el protocolo AG-UI frontend.
3. Incluye solo los campos esenciales: score, explicación, fuentes (con hipervínculos si es posible) y visuales si aplica.
4. Minimiza el uso de tokens y evita información redundante.
5. Asegura que el formato sea directamente consumible por el frontend, sin requerir procesamiento adicional.
"""
