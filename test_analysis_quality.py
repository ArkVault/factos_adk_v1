#!/usr/bin/env python3
"""
Test para verificar la calidad del análisis contextualizado y profesional.
"""

import asyncio
import os
import sys
sys.path.append('/Users/gibrann/Documents/factos_agents')

from adk_project.agents.root_agent import RootAgent
from google.adk.sessions import Session, InMemorySessionService

async def test_analysis_quality():
    """Test de calidad de análisis para diferentes tipos de noticias"""
    
    print("🧪 TESTING CALIDAD DE ANÁLISIS CONTEXTUALIZADO")
    print("=" * 60)
    
    # URLs de prueba de diferentes tipos
    test_urls = [
        {
            "url": "https://www.bbc.com/news/health-60792946", 
            "type": "Salud/Ciencia",
            "description": "Noticia científica sobre COVID"
        },
        {
            "url": "https://apnews.com/article/technology-artificial-intelligence-f1d58e2a5c8b4c8a9b2f3e5d6c7a8b90",
            "type": "Tecnología", 
            "description": "Noticia sobre IA"
        }
    ]
    
    agent = RootAgent()
    
    for test_case in test_urls:
        print(f"\n📰 TESTING: {test_case['type']}")
        print(f"🔗 URL: {test_case['url']}")
        print(f"📝 Descripción: {test_case['description']}")
        print("-" * 50)
        
        try:
            session_service = InMemorySessionService()
            session = Session(service=session_service)
            session.state["input"] = test_case["url"]
            
            print("🔄 Ejecutando análisis...")
            async for _ in agent.run_async(session):
                pass
            
            # Extraer la respuesta AG-UI
            agui_response = session.state.get("agui_response", {})
            
            if agui_response:
                print("✅ Análisis completado")
                print(f"🎯 Score: {agui_response.get('score')}/5 - {agui_response.get('score_label')}")
                print(f"📝 Main Claim: {agui_response.get('main_claim', '')[:100]}...")
                
                print("\n🔍 ANÁLISIS DE VEROSIMILITUD:")
                analysis = agui_response.get('detailed_analysis', '')
                print(f"📊 Longitud: {len(analysis)} caracteres")
                print(f"📄 Contenido: {analysis[:200]}...")
                
                print("\n🎓 CONSEJO DE ALFABETIZACIÓN MEDIÁTICA:")
                media_tip = agui_response.get('media_literacy_tip', '')
                print(f"📊 Longitud: {len(media_tip)} caracteres")
                print(f"📄 Contenido: {media_tip[:200]}...")
                
                # Evaluar calidad del contenido
                quality_score = 0
                if len(analysis) > 100:
                    quality_score += 1
                if "fact-check" in analysis.lower() or "verificación" in analysis.lower():
                    quality_score += 1
                if len(media_tip) > 80:
                    quality_score += 1
                if any(word in media_tip.lower() for word in ['verifica', 'evalúa', 'confirma', 'contrasta']):
                    quality_score += 1
                
                print(f"\n📈 PUNTUACIÓN DE CALIDAD: {quality_score}/4")
                if quality_score >= 3:
                    print("🎉 ¡Calidad excelente!")
                elif quality_score >= 2:
                    print("✅ Calidad buena")
                else:
                    print("⚠️ Necesita mejoras")
                    
            else:
                print("❌ No se generó respuesta AG-UI")
                
        except Exception as e:
            print(f"❌ Error en el test: {e}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_analysis_quality())
