import sys
import pytest
import asyncio
import os
from dotenv import load_dotenv
sys.path.insert(0, '/Users/gibrann/Documents/factos_agents')

# Cargar variables de entorno reales desde .env
load_dotenv()

# Verificar que tenemos las API keys necesarias
required_keys = ['GOOGLE_API_KEY', 'FIRECRAWL_API_KEY', 'GOOGLE_FACTCHECK_API_KEY', 'PERPLEXITY_API_KEY']
missing_keys = [key for key in required_keys if not os.getenv(key)]
if missing_keys:
    print(f"❌ Faltan las siguientes variables de entorno: {missing_keys}")
    print("Por favor, configura el archivo .env correctamente")
    sys.exit(1)

from adk_project.agents.root_agent import RootAgent
from google.adk.sessions import Session, InMemorySessionService
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.run_config import RunConfig
import uuid

@pytest.mark.asyncio
async def test_root_agent_integration():
    """Test de integración completo del RootAgent"""
    
    # URL de prueba (usaremos The Guardian que tiene datos simulados)
    test_url = "https://www.theguardian.com/world/2025/jun/11/uk-and-gibraltar-strike-deal-over-territorys-future-and-borders"
    
    # Crear sesión
    session = Session(
        id=str(uuid.uuid4()),
        app_name="factos-agents-test",
        user_id="test-user",
        state={"input": test_url}
    )
    
    # Crear agente y contexto
    agent = RootAgent()
    session_service = InMemorySessionService()
    ctx = InvocationContext(
        session=session,
        session_service=session_service,
        invocation_id=str(uuid.uuid4()),
        agent=agent,
        run_config=RunConfig()
    )
    
    # Ejecutar el agente
    events = []
    try:
        async for event in agent.run_async(ctx):
            events.append(event)
        
        # Verificar que se completó el proceso
        assert session.state is not None
        assert "agui_response" in session.state
        
        agui_response = session.state["agui_response"]
        print(f"AGUI Response: {agui_response}")
        
        # Verificar estructura básica de la respuesta
        assert isinstance(agui_response, dict)
        
        print("✅ Test de integración completado exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en test de integración: {e}")
        raise e

def test_imports():
    """Test básico de importación de módulos"""
    try:
        from adk_project.agents.claim_extractor_agent.claim_extractor_agent import ClaimExtractorAgent
        from adk_project.agents.fact_check_matcher_agent.fact_check_matcher_agent import FactCheckMatcherAgent
        from adk_project.agents.truth_scorer_agent.truth_scorer_agent import TruthScorerAgent
        from adk_project.agents.response_formatter_agent.response_formatter_agent import ResponseFormatterAgent
        from adk_project.agents.smart_scraper_agent.smart_scraper_agent import SmartScraperAgent
        
        print("✅ Todas las importaciones exitosas")
        return True
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        raise e

if __name__ == "__main__":
    # Ejecutar tests básicos
    test_imports()
    asyncio.run(test_root_agent_integration())
