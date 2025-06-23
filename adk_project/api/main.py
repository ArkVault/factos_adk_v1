from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from adk_project.agents.smart_scraper_agent import SmartScraperAgent
from adk_project.agents.claim_extractor_agent import ClaimExtractorAgent
from adk_project.agents.fact_check_matcher_agent import FactCheckMatcherAgent
from adk_project.agents.truth_scorer_agent import TruthScorerAgent
from adk_project.agents.response_formatter_agent import ResponseFormatterAgent

app = FastAPI(title="News Truth Verification API")

# Input format for a single prediction instance
class PredictionInstance(BaseModel):
    url: str

# The overall request format that Vertex AI sends
class PredictionRequest(BaseModel):
    instances: List[PredictionInstance]

# The response format that Vertex AI expects
class PredictionResponse(BaseModel):
    predictions: List[Dict]

# Define Pydantic models for a mock ADK context, providing the .model_copy() method
class MockSession(BaseModel):
    state: Dict[str, Any] = Field(default_factory=dict)

class MockContext(BaseModel):
    session: MockSession = Field(default_factory=MockSession)

    def start_invocation(self, invocation_spec: Dict[str, Any]) -> None:
        """A dummy start_invocation method for compatibility."""
        pass

    def end_invocation(self) -> None:
        """A dummy end_invocation method for compatibility."""
        pass


@app.post("/verify", response_model=PredictionResponse)
async def verify_news(request: PredictionRequest):
    try:
        if not request.instances:
            raise HTTPException(status_code=400, detail="No instances provided")

        first_instance = request.instances[0]
        url_to_verify = first_instance.url
        
        # Create a mock ADK context
        ctx = MockContext()
        ctx.session.state['input'] = url_to_verify
        
        # --- Manual Agent Orchestration ---
        # Instead of relying on SequentialAgent, we call each agent in order.
        
        print("--- Running SmartScraperAgent ---")
        async for _ in SmartScraperAgent().run_async(ctx):
            pass
        print("State after scrape:", ctx.session.state.keys())

        print("--- Running ClaimExtractorAgent ---")
        async for _ in ClaimExtractorAgent().run_async(ctx):
            pass
        print("State after claims:", ctx.session.state.keys())

        print("--- Running FactCheckMatcherAgent ---")
        async for _ in FactCheckMatcherAgent().run_async(ctx):
            pass
        print("State after matching:", ctx.session.state.keys())

        print("--- Running TruthScorerAgent ---")
        async for _ in TruthScorerAgent().run_async(ctx):
            pass
        print("State after scoring:", ctx.session.state.keys())

        print("--- Running ResponseFormatterAgent ---")
        async for _ in ResponseFormatterAgent().run_async(ctx):
            pass
        print("State after formatting:", ctx.session.state.keys())
        
        agui_response = ctx.session.state.get('agui_response', {})
        return PredictionResponse(predictions=[agui_response])

    except Exception as e:
        # It's helpful to log the full traceback for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"status": "ok"}
