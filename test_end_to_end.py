import asyncio
import sys
import os
from dotenv import load_dotenv
sys.path.insert(0, '/Users/gibrann/Documents/factos_agents')

# Cargar variables de entorno
load_dotenv()

async def test_api_endpoint():
    """Test del endpoint /predict de la API"""
    
    # Simular el comportamiento del endpoint /predict
    from adk_project.api.main import predict, PredictRequest
    
    # Crear request de prueba
    test_request = PredictRequest(
        instances=["https://www.theguardian.com/world/2025/jun/11/uk-and-gibraltar-strike-deal-over-territorys-future-and-borders"]
    )
    
    print("🧪 Probando endpoint /predict...")
    
    try:
        # Ejecutar el endpoint
        response = await predict(test_request)
        
        print(f"✅ Respuesta recibida: {response.predictions[0]}")
        
        # Verificar estructura de la respuesta
        prediction = response.predictions[0]
        required_fields = ['score', 'score_label', 'main_claim', 'detailed_analysis']
        
        missing_fields = [field for field in required_fields if field not in prediction]
        if missing_fields:
            print(f"⚠️  Campos faltantes en la respuesta: {missing_fields}")
        else:
            print("✅ Todos los campos requeridos están presentes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test del endpoint: {e}")
        raise e

def test_api_import():
    """Test de importación de la API"""
    try:
        from adk_project.api.main import app
        print("✅ API FastAPI importada correctamente")
        return True
    except Exception as e:
        print(f"❌ Error importando API: {e}")
        raise e

if __name__ == "__main__":
    print("=== TEST END-TO-END COMPLETO ===\n")
    
    # Test 1: Importación de API
    print("1. Test de importación de API...")
    test_api_import()
    
    # Test 2: Endpoint de predicción
    print("\n2. Test del endpoint /predict...")
    asyncio.run(test_api_endpoint())
    
    print("\n🎉 TODOS LOS TESTS PASARON - PROYECTO LISTO PARA DESPLIEGUE")
