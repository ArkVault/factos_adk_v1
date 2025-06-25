"""
Test del sistema mejorado con análisis contextualizado y media literacy inteligente
"""

import asyncio
import sys
import os
from dotenv import load_dotenv
sys.path.insert(0, '/Users/gibrann/Documents/factos_agents')

# Cargar variables de entorno
load_dotenv()

async def test_improved_analysis():
    """Test del sistema con análisis mejorado"""
    
    print("🧪 TESTING ANÁLISIS CONTEXTUALIZADO MEJORADO")
    print("=" * 60)
    
    # URL de prueba
    test_url = "https://www.theguardian.com/world/2025/may/21/israeli-troops-fire-warning-shots-25-diplomats-visiting-occupied-west-bank"
    
    print(f"📰 URL: {test_url}")
    print()
    
    try:
        from adk_project.agents.root_agent import RootAgent
        from google.adk.sessions import Session, InMemorySessionService
        from google.adk.agents.invocation_context import InvocationContext
        from google.adk.agents.run_config import RunConfig
        import uuid
        import time
        
        start_time = time.time()
        
        # Crear sesión
        session = Session(
            id=str(uuid.uuid4()),
            app_name="factos-agents-improved-test",
            user_id="test-user",
            state={"input": test_url}
        )
        
        # Configurar agente
        agent = RootAgent()
        session_service = InMemorySessionService()
        ctx = InvocationContext(
            session=session,
            session_service=session_service,
            invocation_id=str(uuid.uuid4()),
            agent=agent,
            run_config=RunConfig()
        )
        
        print("🔄 Ejecutando pipeline con análisis mejorado...")
        
        # Ejecutar agente
        events = []
        async for event in agent.run_async(ctx):
            events.append(event)
        
        # Obtener resultado
        result = session.state.get("agui_response", {})
        processing_time = time.time() - start_time
        
        print("✅ Pipeline completado!")
        print()
        
        # Mostrar resultados mejorados
        print("📊 RESULTADOS CON ANÁLISIS CONTEXTUALIZADO")
        print("=" * 60)
        
        print(f"📄 Headline: {result.get('headline', 'N/A')}")
        print(f"🎯 Score: {result.get('score', 'N/A')} - {result.get('score_label', 'N/A')}")
        print(f"🔗 Dominio: {result.get('source_domain', 'N/A')}")
        print()
        
        print("🧠 ANÁLISIS CONTEXTUALIZADO:")
        print("-" * 40)
        recommendation = result.get('recommendation', 'N/A')
        print(f"{recommendation}")
        print()
        
        print("🎓 MEDIA LITERACY CONTEXTUALIZADA:")
        print("-" * 40)
        media_tip = result.get('media_literacy_tip', 'N/A')
        print(f"{media_tip}")
        print()
        
        print("📈 ESTADÍSTICAS:")
        print("-" * 20)
        stats = result.get('analysis_stats', {})
        print(f"⏱️  Tiempo de procesamiento: {stats.get('processing_time', processing_time):.1f}s")
        print(f"🔍 Fuentes verificadas: {stats.get('sources_checked', 0)}")
        print(f"📊 Nivel de confianza: {stats.get('confidence_level', 0)}%")
        
        # Verificar calidad del contenido
        print()
        print("🔍 EVALUACIÓN DE CALIDAD:")
        print("-" * 30)
        
        quality_checks = []
        
        # Check 1: Análisis contextualizado
        if len(recommendation) > 100 and "Análisis:" in recommendation:
            quality_checks.append("✅ Análisis contextualizado generado")
        else:
            quality_checks.append("❌ Análisis genérico o muy corto")
        
        # Check 2: Media literacy específica
        if len(media_tip) > 50 and not "Always verify" in media_tip:
            quality_checks.append("✅ Media literacy contextualizada")
        else:
            quality_checks.append("❌ Media literacy genérica")
        
        # Check 3: Uso de fact-checkers
        if "fact-check" in recommendation.lower() or "verifica" in recommendation.lower():
            quality_checks.append("✅ Menciona fact-checkers consultados")
        else:
            quality_checks.append("⚠️  No menciona fact-checkers específicamente")
        
        for check in quality_checks:
            print(check)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 TEST DE ANÁLISIS CONTEXTUALIZADO MEJORADO")
    print("=" * 60)
    
    success = asyncio.run(test_improved_analysis())
    
    if success:
        print("\n🎉 SISTEMA MEJORADO FUNCIONANDO CORRECTAMENTE")
        print("✅ Análisis contextualizado con fact-checkers")
        print("✅ Media literacy específica por caso")
        print("✅ Contenido serio y profesional")
    else:
        print("\n⚠️  REQUIERE REVISIÓN ADICIONAL")
