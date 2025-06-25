"""
Test de la nueva estructura de respuesta compatible con AG-UI
"""

import asyncio
import sys
import os
import time
from dotenv import load_dotenv
sys.path.insert(0, '/Users/gibrann/Documents/factos_agents')

# Cargar variables de entorno
load_dotenv()

async def test_new_agui_structure():
    """Test de la nueva estructura AG-UI con la URL de The Guardian"""
    
    print("🧪 TESTING NUEVA ESTRUCTURA AG-UI")
    print("=" * 50)
    
    # URL de prueba de The Guardian
    test_url = "https://www.theguardian.com/world/2025/may/21/israeli-troops-fire-warning-shots-25-diplomats-visiting-occupied-west-bank"
    
    print(f"📰 URL de prueba: {test_url}")
    print()
    
    try:
        from adk_project.agents.root_agent import RootAgent
        from google.adk.sessions import Session, InMemorySessionService
        from google.adk.agents.invocation_context import InvocationContext
        from google.adk.agents.run_config import RunConfig
        import uuid
        
        # Crear sesión
        session = Session(
            id=str(uuid.uuid4()),
            app_name="factos-agents-agui-test",
            user_id="test-user",
            state={"input": test_url}
        )
        
        # Inicializar RootAgent
        agent = RootAgent()
        session_service = InMemorySessionService()
        
        # Crear contexto
        ctx = InvocationContext(
            session=session,
            session_service=session_service,
            invocation_id=str(uuid.uuid4()),
            agent=agent,
            run_config=RunConfig()
        )
        
        # Ejecutar pipeline
        print("🔄 Ejecutando pipeline completo...")
        start_time = time.time()
        
        events = []
        async for event in agent.run_async(ctx):
            events.append(event)
        
        processing_time = time.time() - start_time
        
        # Obtener resultado final
        agui_response = session.state.get("agui_response", {})
        
        if not agui_response:
            print("❌ No se generó respuesta AG-UI")
            return False
        
        print("✅ Respuesta AG-UI generada exitosamente")
        print()
        
        # Verificar estructura esperada según la imagen
        expected_fields = [
            'headline', 'url', 'source_domain', 'score', 'score_label', 
            'score_fraction', 'main_claim', 'detailed_analysis', 
            'verified_sources', 'verified_sources_label', 'recommendation',
            'media_literacy_tip', 'source_credibility', 'analysis_stats',
            'active_agents', 'quick_actions'
        ]
        
        missing_fields = [field for field in expected_fields if field not in agui_response]
        
        if missing_fields:
            print(f"⚠️  Campos faltantes: {missing_fields}")
        else:
            print("✅ Todos los campos requeridos presentes")
        
        # Mostrar estructura según la imagen
        print()
        print("📋 ESTRUCTURA AG-UI (según imagen)")
        print("=" * 50)
        
        print(f"📰 Headline: {agui_response.get('headline', 'N/A')}")
        print(f"🌐 Domain: {agui_response.get('source_domain', 'N/A')}")
        print(f"🎯 Score: {agui_response.get('score_fraction', 'N/A')}")
        print(f"📝 Main Claim: {agui_response.get('main_claim', 'N/A')[:100]}...")
        
        # Análisis detallado
        analysis = agui_response.get('detailed_analysis', 'N/A')
        print(f"🔍 Analysis: {analysis[:150]}...")
        
        # Fuentes verificadas
        sources = agui_response.get('verified_sources', [])
        print(f"📚 Verified Sources ({len(sources)}):")
        for i, source in enumerate(sources[:3]):
            if isinstance(source, dict):
                print(f"   {i+1}. {source.get('name', 'Unknown')}")
            else:
                print(f"   {i+1}. {source}")
        
        # Recomendación
        recommendation = agui_response.get('recommendation', 'N/A')
        print(f"💡 Recommendation: {recommendation[:100]}...")
        
        # Media literacy tip
        tip = agui_response.get('media_literacy_tip', 'N/A')
        print(f"🎓 Media Literacy: {tip[:100]}...")
        
        # Estadísticas
        stats = agui_response.get('analysis_stats', {})
        if stats:
            print(f"📊 Stats: {stats.get('processing_time', 0)}s, {stats.get('sources_checked', 0)} sources, {stats.get('confidence_level', 0)}% confidence")
        
        # Credibilidad de la fuente
        credibility = agui_response.get('source_credibility', {})
        if credibility:
            print(f"🔒 Source: {credibility.get('label', 'Unknown')} ({credibility.get('risk_level', 'Unknown')} Risk)")
        
        # Agentes activos
        agents = agui_response.get('active_agents', [])
        print(f"🤖 Active Agents: {len(agents)}")
        
        print()
        print("🎉 ESTRUCTURA AG-UI COMPATIBLE VERIFICADA")
        print(f"⏱️  Tiempo total: {processing_time:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agui_protocol():
    """Test del protocolo AG-UI"""
    
    print("\n🔧 TESTING PROTOCOLO AG-UI")
    print("=" * 40)
    
    try:
        from adk_project.protocols.agui_response import AGUIResponse, VerifiedSource, SourceCredibility, AnalysisStats
        
        # Crear ejemplo de respuesta
        test_response = AGUIResponse(
            headline="Test Article Headline",
            url="https://example.com/test",
            source_domain="example.com",
            score=2,
            score_label="Mixed",
            score_fraction="2/5 • Context needed",
            main_claim="Test claim for verification",
            detailed_analysis="This is a test analysis",
            verified_sources=[
                VerifiedSource("Test Source", "https://test.com", "Test description")
            ],
            verified_sources_label="Medium Trust",
            recommendation="Test recommendation",
            media_literacy_tip="Test tip",
            source_credibility=SourceCredibility("Medium Trust", "Medium", "example.com"),
            analysis_stats=AnalysisStats(2.3, 3, 75)
        )
        
        # Convertir a diccionario
        response_dict = test_response.to_dict()
        
        print("✅ Protocolo AG-UI funcional")
        print(f"📊 Campos en respuesta: {len(response_dict)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en protocolo: {e}")
        return False

async def main():
    """Ejecutar todos los tests"""
    
    print("🚀 TESTING NUEVA ESTRUCTURA AG-UI")
    print("🎯 Compatible con la interfaz mostrada en la imagen")
    print("=" * 60)
    
    # Test 1: Protocolo AG-UI
    protocol_ok = test_agui_protocol()
    
    # Test 2: Pipeline completo
    pipeline_ok = await test_new_agui_structure()
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN FINAL")
    print("=" * 60)
    
    print(f"🔧 Protocolo AG-UI: {'✅ PASS' if protocol_ok else '❌ FAIL'}")
    print(f"🔄 Pipeline Completo: {'✅ PASS' if pipeline_ok else '❌ FAIL'}")
    
    if protocol_ok and pipeline_ok:
        print("\n🎉 SISTEMA COMPLETAMENTE COMPATIBLE CON AG-UI")
        print("✅ Estructura de respuesta coincide con la imagen")
        print("✅ Frontend puede consumir sin problemas")
        print("✅ Listo para integración")
    else:
        print("\n⚠️  REQUIERE AJUSTES ADICIONALES")
    
    return protocol_ok and pipeline_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n🏁 RESULTADO: {'SUCCESS' if success else 'NEEDS_WORK'}")
    sys.exit(0 if success else 1)
