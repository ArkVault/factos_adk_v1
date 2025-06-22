"""
Test para el pipeline RootAgent de verificación de noticias
"""

import asyncio
import pytest
from adk_project.agents.root_agent import RootAgent
from google.adk.sessions import Session, SessionService
from google.adk.agents.invocation_context import InvocationContext

@pytest.mark.asyncio
async def test_root_agent_pipeline():
    # Simula una entrada de usuario (URL de noticia)
    session = Session(input="https://ejemplo.com/noticia-falsa")
    ctx = InvocationContext(session=session)
    agent = RootAgent()

    # Ejecuta el pipeline completo
    events = []
    async for event in agent.run_async(ctx):
        events.append(event)

    # Verifica que el estado final contiene la respuesta AG-UI
    assert "agui_response" in session.state
    print("Respuesta AG-UI:", session.state["agui_response"])
