import os
from dotenv import load_dotenv
import asyncio
import pytest
from adk_project.agents.root_agent import RootAgent
from google.adk.sessions import Session, InMemorySessionService
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.run_config import RunConfig

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

@pytest.mark.asyncio
async def test_real_news_url():
    session = Session(
        id="test-session-real",
        appName="test-app",
        userId="test-user",
        state={"input": "https://www.theguardian.com/world/2025/jun/11/uk-and-gibraltar-strike-deal-over-territorys-future-and-borders"}
    )
    agent = RootAgent()
    session_service = InMemorySessionService()
    ctx = InvocationContext(
        session=session,
        session_service=session_service,
        invocation_id="test-invocation-real",
        agent=agent,
        run_config=RunConfig()
    )
    events = []
    async for event in agent.run_async(ctx):
        events.append(event)
    assert "agui_response" in session.state
    print("Respuesta AG-UI:", session.state["agui_response"])
