#!/usr/bin/env python3
"""
Test simple del API endpoint para verificar funcionamiento
"""

import sys
import time

# Test simple usando el API directamente
def test_api_endpoint():
    """Test del endpoint principal usando imports del proyecto"""
    print("🔍 Iniciando test simple del API...")
    
    try:
        # Importar el endpoint principal
        sys.path.insert(0, './adk_project')
        from api.main import create_fact_check_result
        
        # Test de la función helper
        print("📋 Test 1: Función helper create_fact_check_result...")
        
        test_agui_response = {
            "headline": "Test Article",
            "score": 3,
            "score_label": "Mixed",
            "main_claim": "Test claim",
            "detailed_analysis": "Test analysis",
            "verified_sources": [
                {"name": "Test Source", "url": "https://example.com", "description": "Test"}
            ],
            "verified_sources_label": "Medium Trust",
            "match_type": "derivative",
            "recommendation": "Test recommendation",
            "media_literacy_tip": "Test tip",
            "source_credibility": {
                "label": "High Trust",
                "risk_level": "Low",
                "domain": "example.com"
            },
            "active_agents": [],
            "quick_actions": {}
        }
        
        result = create_fact_check_result(
            agui_response=test_agui_response,
            url="https://example.com/test",
            processing_time=1.5
        )
        
        # Verificar campos requeridos
        required_fields = [
            'headline', 'url', 'source_domain', 'score', 'score_label', 
            'score_fraction', 'main_claim', 'detailed_analysis', 
            'verified_sources', 'verified_sources_label', 'match_type',
            'recommendation', 'media_literacy_tip', 'source_credibility', 
            'analysis_stats', 'active_agents', 'quick_actions'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in result:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ ERROR: Campos faltantes en resultado: {missing_fields}")
            return False
        
        print(f"✅ Función helper funciona correctamente")
        print(f"   Score: {result['score']}/5 ({result['score_label']})")
        print(f"   Match type: {result['match_type']}")
        print(f"   Fuentes: {len(result['verified_sources'])}")
        
        # Test con error
        print("\n📋 Test 2: Función helper con error...")
        
        error_result = create_fact_check_result(
            url="https://example.com/error",
            processing_time=0.5,
            error_info={
                "headline": "Error Test",
                "score_label": "Error",
                "detailed_analysis": "Test error occurred",
                "recommendation": "Please try again",
                "media_literacy_tip": "Always verify sources"
            }
        )
        
        if 'match_type' not in error_result:
            print(f"❌ ERROR: Campo match_type faltante en caso de error")
            return False
        
        print(f"✅ Función helper maneja errores correctamente")
        print(f"   Match type en error: {error_result['match_type']}")
        
        # Test de imports de agentes
        print("\n📋 Test 3: Imports de agentes...")
        
        try:
            from agents.truth_scorer_agent.truth_scorer_agent import TruthScorerAgent
            from agents.response_formatter_agent.response_formatter_agent import ResponseFormatterAgent
            from protocols.agui_response import AGUIResponse
            print("✅ Todos los imports de agentes funcionan")
        except ImportError as e:
            print(f"❌ ERROR en imports: {e}")
            return False
        
        print(f"\n🎉 ¡TESTS BÁSICOS COMPLETADOS EXITOSAMENTE!")
        print(f"✅ API está listo para despliegue")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR en test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api_endpoint()
    
    if success:
        print("\n✅ API LISTO PARA DESPLIEGUE")
        sys.exit(0)
    else:
        print("\n❌ API TIENE ERRORES - NO DESPLEGAR")
        sys.exit(1)
