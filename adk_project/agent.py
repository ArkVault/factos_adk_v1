"""
RootAgent (Orquestador principal)
Orquesta el flujo secuencial de los agentes del sistema de verificación de noticias.
"""

from google.adk.agents import LlmAgent

# This is the object that will be passed to the deployment function.
root_agent = LlmAgent(
    name="FactosAgent",
    instruction="You are a helpful assistant. The user will provide a URL, and you will respond with a simple confirmation message.",
    model="gemini-2.5-flash"
) 