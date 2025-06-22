"""
Test para el pipeline RootAgent de verificación de noticias
"""

import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

import asyncio
import pytest
from adk_project.agents.root_agent import RootAgent
from google.adk.sessions import Session, InMemorySessionService
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.run_config import RunConfig

@pytest.mark.asyncio
async def test_root_agent_pipeline():
    # Simula una entrada de usuario (URL de noticia)
    session = Session(
        id="test-session",
        appName="test-app",
        userId="test-user",
        state={"input": "https://ejemplo.com/noticia-falsa"}
    )
    agent = RootAgent()
    session_service = InMemorySessionService()
    ctx = InvocationContext(
        session=session,
        session_service=session_service,
        invocation_id="test-invocation",
        agent=agent,
        run_config=RunConfig()
    )

    # Ejecuta el pipeline completo
    events = []
    async for event in agent.run_async(ctx):
        events.append(event)

    # Verifica que el estado final contiene la respuesta AG-UI
    assert "agui_response" in session.state
    print("Respuesta AG-UI:", session.state["agui_response"])
