#!/usr/bin/env python3
"""
Test completo del pipeline de fact-checking
Verifica que todos los agentes funcionen correctamente en secuencia
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent / "adk_project"
sys.path.insert(0, str(project_root))

# Importar agentes
from agents.claim_extractor_agent.claim_extractor_agent import ClaimExtractorAgent
from agents.fact_check_matcher_agent.fact_check_matcher_agent import FactCheckMatcherAgent
from agents.truth_scorer_agent.truth_scorer_agent import TruthScorerAgent
from agents.response_formatter_agent.response_formatter_agent import ResponseFormatterAgent

# Mock session para testing
class MockSession:
    def __init__(self):
        self.state = {}

class MockContext:
    def __init__(self, url):
        self.session = MockSession()
        self.session.state["input"] = url

async def test_pipeline_complete():
    """Test completo del pipeline con una URL real"""
    print("🔍 Iniciando test completo del pipeline de fact-checking...")
    
    # URL de prueba
    test_url = "https://www.theguardian.com/world/2025/may/21/israeli-troops-fire-warning-shots-25-diplomats-visiting-occupied-west-bank"
    
    start_time = time.time()
    
    try:
        # 1. Test Claim Extractor Agent
        print("\n📋 Paso 1: Extrayendo claim principal...")
        ctx = MockContext(test_url)
        
        claim_extractor = ClaimExtractorAgent()
        async for _ in claim_extractor.run_async(ctx):
            pass
        
        extracted_claim = ctx.session.state.get("extracted_claim", {})
        print(f"✅ Claim extraído: {extracted_claim.get('claim', 'No encontrado')[:100]}...")
        
        if not extracted_claim.get('claim'):
            print("❌ ERROR: No se pudo extraer el claim")
            return False
        
        # 2. Test Fact Check Matcher Agent
        print("\n🔍 Paso 2: Buscando coincidencias en fact-checkers...")
        
        fact_matcher = FactCheckMatcherAgent()
        async for _ in fact_matcher.run_async(ctx):
            pass
        
        match_results = ctx.session.state.get("match_results", {})
        matches = match_results.get("matches", [])
        print(f"✅ Coincidencias encontradas: {len(matches)}")
        print(f"   Calidad de coincidencias: {match_results.get('match_quality', 'unknown')}")
        
        # 3. Test Truth Scorer Agent
        print("\n🎯 Paso 3: Evaluando veracidad...")
        
        truth_scorer = TruthScorerAgent()
        async for _ in truth_scorer.run_async(ctx):
            pass
        
        scored_result = ctx.session.state.get("scored_result", {})
        print(f"✅ Score asignado: {scored_result.get('score', 'N/A')}/5")
        print(f"   Label: {scored_result.get('label', 'N/A')}")
        print(f"   Match type: {scored_result.get('match_type', 'N/A')}")
        print(f"   Análisis: {scored_result.get('detailed_analysis', 'N/A')[:150]}...")
        
        if scored_result.get('score') is None:
            print("❌ ERROR: No se pudo generar score")
            return False
        
        # 4. Test Response Formatter Agent
        print("\n📋 Paso 4: Formateando respuesta final...")
        
        response_formatter = ResponseFormatterAgent()
        async for _ in response_formatter.run_async(ctx):
            pass
        
        agui_response = ctx.session.state.get("agui_response", {})
        print(f"✅ Respuesta final generada")
        print(f"   Headline: {agui_response.get('headline', 'N/A')[:100]}...")
        print(f"   Score final: {agui_response.get('score', 'N/A')}/5")
        print(f"   Label final: {agui_response.get('score_label', 'N/A')}")
        print(f"   Match type: {agui_response.get('match_type', 'N/A')}")
        print(f"   Fuentes verificadas: {len(agui_response.get('verified_sources', []))}")
        print(f"   Tiempo de procesamiento: {agui_response.get('analysis_stats', {}).get('processing_time', 'N/A')}s")
        
        if not agui_response.get('headline'):
            print("❌ ERROR: No se pudo generar respuesta final")
            return False
        
        # 5. Verificar campos requeridos
        print("\n✅ Paso 5: Verificando campos requeridos...")
        required_fields = [
            'headline', 'url', 'source_domain', 'score', 'score_label', 
            'score_fraction', 'main_claim', 'detailed_analysis', 
            'verified_sources', 'verified_sources_label', 'match_type',
            'recommendation', 'media_literacy_tip', 'source_credibility', 
            'analysis_stats', 'active_agents', 'quick_actions'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in agui_response:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ ERROR: Campos faltantes: {missing_fields}")
            return False
        
        total_time = time.time() - start_time
        print(f"\n🎉 ¡PIPELINE COMPLETADO EXITOSAMENTE!")
        print(f"⏱️  Tiempo total: {total_time:.2f} segundos")
        print(f"📊 Resultado final:")
        print(f"   - Score: {agui_response['score']}/5 ({agui_response['score_label']})")
        print(f"   - Match type: {agui_response['match_type']}")
        print(f"   - Fuentes: {len(agui_response['verified_sources'])}")
        print(f"   - Análisis: {agui_response['detailed_analysis'][:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR en el pipeline: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Configurar variables de entorno si no están configuradas
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  GOOGLE_API_KEY no configurada, usando variables del archivo .env")
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            print("❌ dotenv no disponible, asegúrate de que las variables estén configuradas")
    
    # Ejecutar test
    success = asyncio.run(test_pipeline_complete())
    
    if success:
        print("\n✅ PIPELINE LISTO PARA DESPLIEGUE")
        sys.exit(0)
    else:
        print("\n❌ PIPELINE TIENE ERRORES - NO DESPLEGAR")
        sys.exit(1)
