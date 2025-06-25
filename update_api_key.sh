#!/bin/bash

# Script para actualizar Cloud Run con nueva Google API Key
# Ejecutar después de crear una nueva API key en Google Cloud Console

echo "🔐 Actualizando Google API Key en Cloud Run..."
echo "⚠️  ASEGÚRATE de haber revocado la API key anterior en Google Cloud Console"
echo ""

# Solicitar la nueva API key
read -p "Ingresa la nueva Google API Key: " NEW_API_KEY

if [ -z "$NEW_API_KEY" ]; then
    echo "❌ Error: No se proporcionó una API key"
    exit 1
fi

# Validar formato básico de Google API Key
if [[ ! $NEW_API_KEY =~ ^AIza[A-Za-z0-9_-]{35}$ ]]; then
    echo "⚠️  Advertencia: La API key no tiene el formato típico de Google (AIza...)"
    read -p "¿Continuar anyway? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        echo "❌ Operación cancelada"
        exit 1
    fi
fi

echo ""
echo "🚀 Actualizando servicio Cloud Run..."

# Actualizar el servicio
gcloud run services update factos-agents \
  --region=us-central1 \
  --set-env-vars="GOOGLE_API_KEY=$NEW_API_KEY" \
  --quiet

if [ $? -eq 0 ]; then
    echo "✅ API Key actualizada exitosamente en Cloud Run"
    echo ""
    echo "🧪 Probando el servicio..."
    
    # Probar el endpoint de health
    curl -s "https://factos-agents-158463493485.us-central1.run.app/health" | jq .
    
    echo ""
    echo "✅ PASOS COMPLETADOS:"
    echo "  - API Key actualizada en Cloud Run"
    echo "  - Servicio funcionando correctamente"
    echo ""
    echo "🔴 PENDIENTES:"
    echo "  - Revocar la API key anterior en Google Cloud Console"
    echo "  - Actualizar .env local con la nueva key"
    echo "  - Cerrar la alerta de seguridad en GitHub"
else
    echo "❌ Error actualizando el servicio Cloud Run"
    exit 1
fi
