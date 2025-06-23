from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Any
from adk_project.agents.root_agent import RootAgent
from google.adk.sessions import Session, InMemorySessionService
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.run_config import RunConfig
import uuid
import asyncio

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

# --- Agrega esto ---
class PredictRequest(BaseModel):
    instances: List[Any]

class PredictResponse(BaseModel):
    predictions: List[Any]

@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    # Solo se procesa la primera instancia (URL)
    url = request.instances[0] if request.instances else None
    if not url:
        return PredictResponse(predictions=[{"error": "No input provided"}])

    session = Session(
        id=str(uuid.uuid4()),
        app_name="factos-agents-api",
        user_id="api-user",
        state={"input": url}
    )
    agent = RootAgent()
    session_service = InMemorySessionService()
    ctx = InvocationContext(
        session=session,
        session_service=session_service,
        invocation_id=str(uuid.uuid4()),
        agent=agent,
        run_config=RunConfig()
    )
    events = []
    async for event in agent.run_async(ctx):
        events.append(event)
    print("DEBUG session.state:", session.state)
    agui_response = session.state.get("agui_response", {"error": "No AG-UI response"})
    return PredictResponse(predictions=[agui_response])
# --- Fin de lo nuevo ---