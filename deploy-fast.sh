#!/bin/bash

# Script de despliegue simplificado para Google Cloud Run
# Usa variables de entorno en lugar de Secret Manager para mayor velocidad

set -e

echo "🚀 DESPLIEGUE RÁPIDO A GOOGLE CLOUD RUN"
echo "======================================="

# Configuración
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
REGION="us-central1"
SERVICE_NAME="factos-agents"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "✅ Proyecto: $PROJECT_ID"
echo "✅ Región: $REGION"
echo "✅ Servicio: $SERVICE_NAME"

# Verificar PROJECT_ID
if [ -z "$PROJECT_ID" ]; then
    echo "❌ PROJECT_ID no configurado. Ejecuta: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

# Leer API keys del archivo .env
if [ -f .env ]; then
    echo "✅ Leyendo variables de entorno..."
    source .env
else
    echo "❌ Archivo .env no encontrado."
    exit 1
fi

# Habilitar APIs necesarias
echo ""
echo "🔧 Habilitando APIs básicas..."
gcloud services enable run.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID
gcloud services enable containerregistry.googleapis.com --project=$PROJECT_ID

# Construir la imagen Docker
echo ""
echo "🐳 Construyendo imagen Docker..."
gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID .

# Desplegar a Cloud Run usando variables de entorno directamente
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
    --set-env-vars "PYTHONPATH=/app,GOOGLE_API_KEY=${GOOGLE_API_KEY},FIRECRAWL_API_KEY=${FIRECRAWL_API_KEY},PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY}" \
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
echo "curl -X GET \"$SERVICE_URL/health\""
echo "curl -X POST \"$SERVICE_URL/fact-check\" -H \"Content-Type: application/json\" -d '{\"url\": \"https://example.com/news-article\"}'"
echo ""
echo "✅ Sistema optimizado desplegado en Cloud Run!"
