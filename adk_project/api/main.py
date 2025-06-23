from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from adk_project.agent import root_agent

app = FastAPI()

# Pydantic models for request validation
class Instance(BaseModel):
    text: str

class PredictionPayload(BaseModel):
    instances: List[Instance]

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/predict")
def predict(payload: PredictionPayload):
    predictions = [root_agent.run(instance.text) for instance in payload.instances]
    return {"predictions": predictions}

@app.get("/")
def read_root():
    return {"Hello": "World"}