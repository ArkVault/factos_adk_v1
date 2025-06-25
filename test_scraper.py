#!/usr/bin/env python3
"""
Test del fact-checker scraper para verificar que está encontrando información relevante.
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# Agregar el directorio del proyecto al path
sys.path.insert(0, str(Path(__file__).parent))

from adk_project.agents.fact_check_matcher_agent.factchecker_scraper import get_factchecker_claims, extract_key_terms
from adk_project.agents.fact_check_matcher_agent.fact_check_matcher_agent import semantic_match_with_gemini

async def test_scraper_functionality():
    """Test completo del scraper de fact-checkers"""
    
    print("🔍 PRUEBA DEL FACT-CHECKER SCRAPER")
    print("=" * 50)
    
    # Test 1: Verificar variables de entorno
    print("\n1. VERIFICANDO VARIABLES DE ENTORNO:")
    required_keys = ['GOOGLE_API_KEY', 'FIRECRAWL_API_KEY']
    for key in required_keys:
        value = os.environ.get(key)
        if value:
            print(f"   ✅ {key}: {'*' * 10}{value[-4:]}")
        else:
            print(f"   ❌ {key}: NO CONFIGURADA")
            return False
    
    # Test 2: Extracción de términos clave
    test_claim = "Israeli troops fire warning shots at 25 diplomats visiting occupied West Bank"
    print(f"\n2. EXTRAYENDO TÉRMINOS CLAVE:")
    print(f"   Claim: {test_claim}")
    
    try:
        key_terms = await extract_key_terms(test_claim)
        print(f"   ✅ Términos extraídos: {key_terms}")
    except Exception as e:
        print(f"   ❌ Error extrayendo términos: {e}")
        return False
    
    # Test 3: Búsqueda en fact-checkers
    print(f"\n3. BUSCANDO EN FACT-CHECKERS:")
    print(f"   Esto puede tomar 30-60 segundos...")
    
    try:
        claims = await get_factchecker_claims(test_claim)
        
        print(f"   ✅ Claims encontrados: {len(claims)}")
        
        if claims:
            print(f"\n   RESULTADOS DETALLADOS:")
            for i, claim in enumerate(claims[:3]):  # Solo mostrar los primeros 3
                print(f"   \n   🔎 Resultado #{i+1}:")
                print(f"      URL: {claim.get('url', 'N/A')}")
                print(f"      Source: {claim.get('source', 'N/A')}")
                print(f"      Headline: {claim.get('headline', 'N/A')[:80]}...")
                print(f"      Semantic Score: {claim.get('semantic_score', 'N/A')}")
                print(f"      Relation Type: {claim.get('relation_type', 'N/A')}")
                print(f"      Confidence: {claim.get('confidence', 'N/A')}")
                
                if claim.get('relevance_reason'):
                    print(f"      Relevance: {claim.get('relevance_reason')[:100]}...")
        else:
            print(f"   ⚠️  NO se encontraron claims relevantes")
            
    except Exception as e:
        print(f"   ❌ Error en búsqueda: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Análisis semántico
    if claims:
        print(f"\n4. PROBANDO ANÁLISIS SEMÁNTICO:")
        try:
            semantic_result = await semantic_match_with_gemini(test_claim, claims[:2])
            
            print(f"   ✅ Análisis semántico completado")
            print(f"   Matches semánticos: {len(semantic_result.get('semantic_matches', []))}")
            print(f"   Explicación: {semantic_result.get('explanation', 'N/A')[:100]}...")
            
            for match in semantic_result.get('semantic_matches', [])[:2]:
                print(f"   \n   🧠 Match semántico:")
                print(f"      Source: {match.get('source', 'N/A')}")
                print(f"      Relation: {match.get('relation_type', 'N/A')}")
                print(f"      Confidence: {match.get('confidence_level', 'N/A')}")
                print(f"      Explanation: {match.get('explanation', 'N/A')[:80]}...")
                
        except Exception as e:
            print(f"   ❌ Error en análisis semántico: {e}")
            return False
    
    print(f"\n🎉 TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
    return True

async def test_with_different_claims():
    """Probar con diferentes tipos de claims"""
    
    test_claims = [
        "Coffee prevents cancer according to new study",
        "Donald Trump won 2020 election fraud claims",
        "COVID-19 vaccines contain microchips tracking devices"
    ]
    
    print(f"\n\n🧪 PROBANDO CON DIFERENTES TIPOS DE CLAIMS")
    print("=" * 50)
    
    for i, claim in enumerate(test_claims):
        print(f"\n📋 Test #{i+1}: {claim}")
        
        try:
            claims = await get_factchecker_claims(claim)
            print(f"   ✅ Encontrados: {len(claims)} claims")
            
            if claims:
                best_claim = claims[0]
                print(f"   🏆 Mejor match:")
                print(f"      Score: {best_claim.get('semantic_score', 'N/A')}")
                print(f"      Source: {best_claim.get('source', 'N/A')}")
                print(f"      Relation: {best_claim.get('relation_type', 'N/A')}")
            else:
                print(f"   ⚠️  Sin resultados relevantes")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def main():
    """Función principal"""
    print("🚀 INICIANDO PRUEBAS DEL FACT-CHECKER SCRAPER")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('.env'):
        print("❌ No se encontró archivo .env. Ejecuta desde el directorio raíz del proyecto.")
        return
    
    # Cargar variables de entorno
    try:
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    except Exception as e:
        print(f"❌ Error cargando .env: {e}")
        return
    
    # Ejecutar pruebas
    success = await test_scraper_functionality()
    
    if success:
        await test_with_different_claims()
    
    print(f"\n✅ PRUEBAS FINALIZADAS")

if __name__ == "__main__":
    asyncio.run(main())
