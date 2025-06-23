from fastapi import FastAPI, Request
from adk_project.agent import root_agent
import asyncio

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/predict")
async def predict(request: Request):
    body = await request.json()
    instances = body["instances"]
    
    # Run the agent predictions concurrently, passing only the text
    prediction_tasks = [root_agent.run_async(instance['text']) for instance in instances]
    predictions = await asyncio.gather(*prediction_tasks)
    
    return {"predictions": predictions}

@app.get("/")
def read_root():
    return {"Hello": "World"} 