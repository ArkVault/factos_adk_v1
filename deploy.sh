#!/bin/bash

# Script de despliegue automatizado para Google Cloud Run
# Factos Agents - Sistema de Fact-Checking Optimizado

set -e

echo "🚀 INICIANDO DESPLIEGUE A GOOGLE CLOUD RUN"
echo "=========================================="

# Configuración
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
REGION="us-central1"
SERVICE_NAME="factos-agents"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Verificar que estamos autenticados
echo "🔐 Verificando autenticación con Google Cloud..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ No hay cuenta activa. Ejecuta: gcloud auth login"
    exit 1
fi

# Verificar PROJECT_ID
if [ -z "$PROJECT_ID" ]; then
    echo "❌ PROJECT_ID no configurado. Ejecuta: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "✅ Proyecto: $PROJECT_ID"
echo "✅ Región: $REGION"
echo "✅ Servicio: $SERVICE_NAME"

# Habilitar APIs necesarias
echo ""
echo "🔧 Habilitando APIs necesarias..."
gcloud services enable run.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID
gcloud services enable containerregistry.googleapis.com --project=$PROJECT_ID
gcloud services enable secretmanager.googleapis.com --project=$PROJECT_ID

echo "⏰ Esperando que las APIs se activen (30 segundos)..."
sleep 30

# Crear secretos para las API keys
echo ""
echo "🔐 Configurando secretos..."

# Leer variables del archivo .env
if [ -f .env ]; then
    echo "✅ Archivo .env encontrado, creando secretos..."
    
    # Extraer GOOGLE_API_KEY
    GOOGLE_API_KEY=$(grep "^GOOGLE_API_KEY=" .env | cut -d '=' -f2 | tr -d '"')
    if [ ! -z "$GOOGLE_API_KEY" ]; then
        echo "$GOOGLE_API_KEY" | gcloud secrets create google-api-key --data-file=- --project=$PROJECT_ID 2>/dev/null || \
        echo "$GOOGLE_API_KEY" | gcloud secrets versions add google-api-key --data-file=- --project=$PROJECT_ID
        echo "✅ GOOGLE_API_KEY configurado"
    fi
    
    # Extraer FIRECRAWL_API_KEY
    FIRECRAWL_API_KEY=$(grep "^FIRECRAWL_API_KEY=" .env | cut -d '=' -f2 | tr -d '"')
    if [ ! -z "$FIRECRAWL_API_KEY" ]; then
        echo "$FIRECRAWL_API_KEY" | gcloud secrets create firecrawl-api-key --data-file=- --project=$PROJECT_ID 2>/dev/null || \
        echo "$FIRECRAWL_API_KEY" | gcloud secrets versions add firecrawl-api-key --data-file=- --project=$PROJECT_ID
        echo "✅ FIRECRAWL_API_KEY configurado"
    fi
    
    # Extraer PERPLEXITY_API_KEY
    PERPLEXITY_API_KEY=$(grep "^PERPLEXITY_API_KEY=" .env | cut -d '=' -f2 | tr -d '"')
    if [ ! -z "$PERPLEXITY_API_KEY" ]; then
        echo "$PERPLEXITY_API_KEY" | gcloud secrets create perplexity-api-key --data-file=- --project=$PROJECT_ID 2>/dev/null || \
        echo "$PERPLEXITY_API_KEY" | gcloud secrets versions add perplexity-api-key --data-file=- --project=$PROJECT_ID
        echo "✅ PERPLEXITY_API_KEY configurado"
    fi
else
    echo "❌ Archivo .env no encontrado. Asegúrate de tener las API keys configuradas."
    exit 1
fi

# Construir la imagen Docker
echo ""
echo "🐳 Construyendo imagen Docker..."
gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID .

# Desplegar a Cloud Run
echo ""
echo "☁️ Desplegando a Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 4Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --concurrency 100 \
    --set-env-vars "PORT=8080,PYTHONPATH=/app" \
    --set-secrets "GOOGLE_API_KEY=google-api-key:latest,FIRECRAWL_API_KEY=firecrawl-api-key:latest,PERPLEXITY_API_KEY=perplexity-api-key:latest" \
    --project=$PROJECT_ID

# Obtener URL del servicio
echo ""
echo "🔗 Obteniendo URL del servicio..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)' --project=$PROJECT_ID)

echo ""
echo "🎉 ¡DESPLIEGUE COMPLETADO EXITOSAMENTE!"
echo "=========================================="
echo "📡 URL del servicio: $SERVICE_URL"
echo "🔧 Panel de control: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/overview?project=$PROJECT_ID"
echo ""
echo "🧪 Prueba el servicio:"
echo "curl -X GET \"$SERVICE_URL/\""
echo "curl -X POST \"$SERVICE_URL/fact-check\" -H \"Content-Type: application/json\" -d '{\"url\": \"https://example.com/news-article\"}'"
echo ""
echo "📊 Monitoreo:"
echo "gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --project=$PROJECT_ID"
echo ""
echo "✅ El sistema optimizado está listo para procesar fact-checks en producción!"
