import os
import vertexai
from dotenv import load_dotenv
from adk_project.agent import root_agent
from vertexai import agent_engines
from vertexai.preview import reasoning_engines

# Load environment variables from .env file
load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
STAGING_BUCKET = os.getenv("STAGING_BUCKET")

def deploy_agent():
    """Deploys the RootAgent to Vertex AI Agent Engine."""
    
    print(f"Initializing Vertex AI for project '{PROJECT_ID}' in '{LOCATION}'...")
    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION,
        staging_bucket=STAGING_BUCKET,
    )

    print("Preparing agent for Agent Engine deployment...")
    app = reasoning_engines.AdkApp(agent=root_agent)

    print("Reading project requirements...")
    # The 'requirements' argument tells Agent Engine what to pip install.
    # The '-e .' line in requirements.txt will install our local project.
    with open('requirements.txt', 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    print("Starting agent deployment to Agent Engine. This may take several minutes...")
    remote_app = agent_engines.create(
        agent_engine=app,
        requirements=requirements,
        display_name="Factos ADK Agent",
    )

    resource_name = remote_app.resource_name
    print(f"✅ Agent deployed successfully!")
    print(f"Resource Name: {resource_name}")
    
    return resource_name

if __name__ == "__main__":
    deploy_agent() 