#!/usr/bin/env python3
"""
Test rápido para verificar la calidad del análisis contextualizado.
"""

import asyncio
import os
import sys
sys.path.append('/Users/gibrann/Documents/factos_agents')

from adk_project.agents.response_formatter_agent.response_formatter_agent import ResponseFormatterAgent

async def test_analysis_methods():
    """Test directo de los métodos de análisis mejorados"""
    
    print("🧪 TESTING MÉTODOS DE ANÁLISIS CONTEXTUALIZADO")
    print("=" * 60)
    
    formatter = ResponseFormatterAgent()
    
    # Test 1: Análisis de verosimilitud
    print("\n📊 TEST 1: ANÁLISIS DE VEROSIMILITUD")
    print("-" * 40)
    
    test_claim = "Un nuevo estudio muestra que el ejercicio reduce el riesgo de cáncer en un 50%"
    fake_matches = {
        'matches': [
            {
                'source': 'FactCheck.org',
                'relation_type': 'relacionado',
                'confidence': 'medio',
                'main_claim': 'Estudios muestran beneficios del ejercicio contra el cáncer'
            }
        ],
        'semantic_analysis': {
            'explanation': 'Se encontraron estudios relacionados pero con cifras diferentes'
        }
    }
    
    analysis = formatter._generate_recommendation(
        score=3,
        main_claim=test_claim,
        detailed_analysis="Análisis técnico de ejemplo",
        fact_check_results=fake_matches
    )
    
    print(f"📝 Claim: {test_claim}")
    print(f"🔍 Análisis generado ({len(analysis)} caracteres):")
    print(f"📄 {analysis}")
    
    # Test 2: Consejo de alfabetización mediática
    print("\n🎓 TEST 2: CONSEJO DE ALFABETIZACIÓN MEDIÁTICA")
    print("-" * 40)
    
    media_tip = formatter._generate_media_literacy_tip(
        score=3,
        main_claim=test_claim,
        article_domain="healthnews.com"
    )
    
    print(f"📝 Claim: {test_claim}")
    print(f"🌐 Dominio: healthnews.com") 
    print(f"💡 Consejo generado ({len(media_tip)} caracteres):")
    print(f"📄 {media_tip}")
    
    # Test 3: Análisis sin matches (caso más común)
    print("\n🔍 TEST 3: ANÁLISIS SIN MATCHES DE FACT-CHECKERS")
    print("-" * 40)
    
    no_matches = {'matches': [], 'semantic_analysis': {'explanation': 'No se encontraron verificaciones relacionadas'}}
    
    analysis_no_match = formatter._generate_recommendation(
        score=2,
        main_claim="Los diplomáticos fueron evacuados tras escuchar disparos",
        detailed_analysis="Evento reportado por múltiples fuentes",
        fact_check_results=no_matches
    )
    
    print(f"📝 Claim: Diplomáticos evacuados tras disparos")
    print(f"🔍 Análisis sin matches ({len(analysis_no_match)} caracteres):")
    print(f"📄 {analysis_no_match}")
    
    print("\n" + "=" * 60)
    print("✅ TESTS DE ANÁLISIS COMPLETADOS")
    
    # Evaluación de calidad
    print("\n📈 EVALUACIÓN DE CALIDAD:")
    
    quality_metrics = {
        "Longitud adecuada (>100 chars)": len(analysis) > 100 and len(media_tip) > 80,
        "Menciona fact-checking": "fact-check" in analysis.lower() or "verificación" in analysis.lower(),
        "Específico al claim": "estudio" in analysis.lower() or "ejercicio" in analysis.lower(),
        "Consejo práctico": any(word in media_tip.lower() for word in ['verifica', 'evalúa', 'confirma']),
        "Tono profesional": "Análisis" in analysis and not "genéric" in analysis.lower()
    }
    
    for metric, passed in quality_metrics.items():
        status = "✅" if passed else "❌"
        print(f"{status} {metric}")
    
    score = sum(quality_metrics.values()) / len(quality_metrics)
    print(f"\n🎯 PUNTUACIÓN GENERAL: {score:.1%}")
    
    if score >= 0.8:
        print("🎉 ¡Excelente calidad!")
    elif score >= 0.6:
        print("✅ Buena calidad")
    else:
        print("⚠️ Necesita mejoras")

if __name__ == "__main__":
    asyncio.run(test_analysis_methods())
