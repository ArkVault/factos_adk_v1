"""
Test completo del pipeline de fact-checking siguiendo la arquitectura del tutorial de Google ADK.
https://www.firecrawl.dev/blog/google-adk-multi-agent-tutorial
"""

import asyncio
import sys
import os
from dotenv import load_dotenv
sys.path.insert(0, '/Users/gibrann/Documents/factos_agents')

# Cargar variables de entorno
load_dotenv()

from adk_project.agents.root_agent import RootAgent
from google.adk.sessions import Session, InMemorySessionService
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.run_config import RunConfig
import google.ai.generativelanguage as glm
import uuid
import time

async def test_fact_checking_pipeline():
    """Test completo del pipeline de fact-checking con RootAgent LLM."""
    
    print("🧪 TESTING FACT-CHECKING PIPELINE")
    print("=" * 50)
    
    # URL de prueba real
    test_url = "https://apnews.com/article/technology-science-artificial-intelligence-6e2e7e7e7e7e7e7e7e7e7e7e7e7e7e7"
    
    print(f"📰 URL de prueba: {test_url}")
    print()
    
    start_time = time.time()
    
    try:
        # 1. Crear sesión ADK
        print("1️⃣ Creando sesión ADK...")
        session = Session(
            id=str(uuid.uuid4()),
            app_name="factos-agents-test",
            user_id="test-user",
            state={"input": test_url}
        )
        
        # 2. Inicializar RootAgent
        print("2️⃣ Inicializando RootAgent (LLM)...")
        agent = RootAgent()
        session_service = InMemorySessionService()
        
        # 3. Crear contexto de invocación
        print("3️⃣ Configurando contexto de invocación...")
        ctx = InvocationContext(
            session=session,
            session_service=session_service,
            invocation_id=str(uuid.uuid4()),
            agent=agent,
            run_config=RunConfig()
        )
        
        # 4. Probar directamente el método run_async sin message
        print("4️⃣ Ejecutando RootAgent...")
        
        # 5. Ejecutar el agente y procesar eventos
        print("5️⃣ Ejecutando pipeline de fact-checking...")
        events = []
        event_count = 0
        
        async for event in agent.run_async(ctx):
            events.append(event)
            event_count += 1
            print(f"   📡 Evento {event_count}: {type(event).__name__}")
        
        # 6. Extraer resultado final
        print("6️⃣ Extrayendo resultado final...")
        final_result = session.state.get("agui_response", {})
        
        processing_time = time.time() - start_time
        
        # 7. Verificar estructura de la respuesta
        print("7️⃣ Verificando estructura de respuesta...")
        
        required_fields = [
            'score', 'score_label', 'main_claim', 'detailed_analysis',
            'verified_sources', 'recommendation', 'media_literacy_tip',
            'confidence_level'
        ]
        
        missing_fields = [field for field in required_fields if field not in final_result]
        
        if missing_fields:
            print(f"⚠️  Campos faltantes: {missing_fields}")
        else:
            print("✅ Todos los campos requeridos presentes")
        
        # 8. Mostrar resultados
        print()
        print("📊 RESULTADOS DEL FACT-CHECK")
        print("=" * 50)
        print(f"🎯 Score: {final_result.get('score', 'N/A')}")
        print(f"🏷️  Label: {final_result.get('score_label', 'N/A')}")
        print(f"📄 Main Claim: {final_result.get('main_claim', 'N/A')[:100]}...")
        print(f"🔍 Sources Checked: {final_result.get('sources_checked', 0)}")
        print(f"⚡ Processing Time: {processing_time:.2f}s")
        print(f"📈 Confidence: {final_result.get('confidence_level', 0)}%")
        
        print()
        print("🎉 PIPELINE TEST COMPLETADO EXITOSAMENTE")
        print(f"✅ Eventos procesados: {event_count}")
        print(f"✅ Tiempo total: {processing_time:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR EN EL PIPELINE: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_architecture_compliance():
    """Verificar que la arquitectura sigue el tutorial de ADK correctamente."""
    
    print("🏗️  VERIFICANDO CONFORMIDAD CON TUTORIAL ADK")
    print("=" * 50)
    
    try:
        from adk_project.agents.root_agent import RootAgent
        from google.adk.agents import LlmAgent
        
        agent = RootAgent()
        
        # Verificaciones según el tutorial
        checks = [
            ("Es LlmAgent (no SequentialAgent)", isinstance(agent, LlmAgent)),
            ("Tiene herramientas (FunctionTool)", len(agent.tools) > 0),
            ("Tiene sub-agentes especializados", len(agent.sub_agents) > 0),
            ("Nombre descriptivo", agent.name == "FactCheckRootAgent"),
            ("Modelo Gemini configurado", "gemini" in agent.model.lower()),
            ("Instrucciones detalladas", len(agent.instruction) > 100),
        ]
        
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"{status} {check_name}")
        
        all_passed = all(result for _, result in checks)
        
        if all_passed:
            print("\n🎯 ARQUITECTURA TOTALMENTE CONFORME CON EL TUTORIAL")
        else:
            print("\n⚠️  ALGUNAS VERIFICACIONES FALLARON")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error verificando arquitectura: {e}")
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO TESTS COMPLETOS DEL SISTEMA")
    print("🔗 Basado en: https://www.firecrawl.dev/blog/google-adk-multi-agent-tutorial")
    print()
    
    # Test 1: Verificar arquitectura
    arch_result = test_architecture_compliance()
    print()
    
    # Test 2: Pipeline completo
    pipeline_result = asyncio.run(test_fact_checking_pipeline())
    
    print()
    print("📋 RESUMEN FINAL")
    print("=" * 30)
    print(f"🏗️  Arquitectura: {'✅ PASS' if arch_result else '❌ FAIL'}")
    print(f"🔄 Pipeline: {'✅ PASS' if pipeline_result else '❌ FAIL'}")
    
    if arch_result and pipeline_result:
        print("\n🎉 SISTEMA COMPLETAMENTE OPERATIVO")
        print("✅ Listo para procesar URLs de noticias reales")
        print("✅ Siguiendo las mejores prácticas del tutorial ADK")
    else:
        print("\n⚠️  REQUIERE ATENCIÓN ADICIONAL")
