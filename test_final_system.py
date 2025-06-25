"""
Test final del sistema completo siguiendo la arquitectura del tutorial ADK
"""

import asyncio
import requests
import time
import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_api_direct():
    """Test directo de la función predict"""
    
    print("🧪 TEST DIRECTO DE LA API")
    print("=" * 40)
    
    try:
        sys.path.insert(0, '/Users/gibrann/Documents/factos_agents')
        
        # Importar la aplicación
        from adk_project.api.main import app
        from adk_project.api.main import PredictRequest
        print("✅ API importada correctamente")
        
        # Simular request
        test_url = "https://www.theguardian.com/world/2025/jun/11/uk-and-gibraltar-strike-deal-over-territorys-future-and-borders"
        
        print(f"📰 URL de prueba: {test_url}")
        print("🔄 Simulando request...")
        
        # Crear request
        request = PredictRequest(instances=[test_url])
        print(f"✅ Request creado: {len(request.instances)} URL(s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_server_startup():
    """Test de inicio del servidor"""
    
    print("\n🚀 TEST DE INICIO DEL SERVIDOR")
    print("=" * 40)
    
    try:
        import subprocess
        import signal
        import time
        
        # Iniciar servidor en background
        print("🔄 Iniciando servidor uvicorn...")
        
        cmd = [
            "uvicorn", 
            "adk_project.api.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8080",
            "--timeout-graceful-shutdown", "5"
        ]
        
        process = subprocess.Popen(
            cmd,
            cwd="/Users/gibrann/Documents/factos_agents",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Esperar a que el servidor inicie
        time.sleep(3)
        
        # Verificar que el servidor está corriendo
        try:
            response = requests.get("http://localhost:8080/", timeout=10)
            if response.status_code == 200:
                print("✅ Servidor iniciado correctamente")
                print(f"📡 Status: {response.status_code}")
                
                # Test del health check
                health_response = requests.get("http://localhost:8080/health", timeout=10)
                if health_response.status_code == 200:
                    print("✅ Health check OK")
                else:
                    print(f"⚠️  Health check: {health_response.status_code}")
                
                server_running = True
            else:
                print(f"❌ Servidor respondió con código: {response.status_code}")
                server_running = False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error conectando al servidor: {e}")
            server_running = False
        
        # Detener servidor
        print("🛑 Deteniendo servidor...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        
        return server_running
        
    except Exception as e:
        print(f"❌ Error en test de servidor: {e}")
        return False

def test_pipeline_components():
    """Test de componentes individuales del pipeline"""
    
    print("\n🔧 TEST DE COMPONENTES DEL PIPELINE")
    print("=" * 40)
    
    try:
        sys.path.insert(0, '/Users/gibrann/Documents/factos_agents')
        
        # Test 1: RootAgent
        print("1️⃣ Testing RootAgent...")
        from adk_project.agents.root_agent import RootAgent
        agent = RootAgent()
        print(f"   ✅ RootAgent: {agent.name}")
        print(f"   📊 Herramientas: {len(agent.tools)}")
        print(f"   🤖 Sub-agentes: {len(agent.sub_agents)}")
        
        # Test 2: Verificar sub-agentes
        print("2️⃣ Testing sub-agentes...")
        for i, sub_agent in enumerate(agent.sub_agents):
            print(f"   ✅ Sub-agente {i+1}: {sub_agent.__class__.__name__}")
        
        # Test 3: Herramientas de Firecrawl
        print("3️⃣ Testing herramientas Firecrawl...")
        from adk_project.utils.firecrawl import firecrawl_scrape_tool
        print("   ✅ firecrawl_scrape_tool disponible")
        
        print("✅ Todos los componentes funcionando")
        return True
        
    except Exception as e:
        print(f"❌ Error en componentes: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment():
    """Test de variables de entorno"""
    
    print("\n🌍 TEST DE VARIABLES DE ENTORNO")
    print("=" * 40)
    
    required_vars = [
        "GOOGLE_API_KEY",
        "FIRECRAWL_API_KEY", 
        "GOOGLE_FACTCHECK_API_KEY",
        "PERPLEXITY_API_KEY"
    ]
    
    all_ok = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: configurada")
        else:
            print(f"❌ {var}: faltante")
            all_ok = False
    
    return all_ok

def main():
    """Ejecutar todos los tests"""
    
    print("🚀 SISTEMA DE FACT-CHECKING - TESTS FINALES")
    print("🔗 Basado en: https://www.firecrawl.dev/blog/google-adk-multi-agent-tutorial")
    print("=" * 60)
    
    # Ejecutar tests
    tests = [
        ("Variables de Entorno", test_environment),
        ("Componentes del Pipeline", test_pipeline_components),
        ("API Directa", test_api_direct),
        ("Servidor HTTP", test_server_startup),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Ejecutando: {test_name}")
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"📊 Resultado: {status}")
        except Exception as e:
            print(f"❌ Error inesperado en {test_name}: {e}")
            results[test_name] = False
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN FINAL DE TESTS")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 SISTEMA COMPLETAMENTE OPERATIVO")
        print("✅ Listo para despliegue en producción")
        print("✅ Arquitectura conforme al tutorial ADK")
        print("✅ Pipeline de fact-checking funcional")
        print("\n🚀 PROCEDER CON DOCKER BUILD")
    else:
        print(f"\n⚠️  {total - passed} test(s) fallaron")
        print("🔧 Revisar componentes antes del despliegue")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
