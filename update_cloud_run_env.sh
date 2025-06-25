#!/bin/bash

# Script para actualizar todas las variables de entorno en Cloud Run
# Remediación de seguridad - Factos Agents

echo "🔧 Actualizando variables de entorno en Cloud Run..."

# Leer variables del archivo .env
if [ ! -f ".env" ]; then
    echo "❌ Error: archivo .env no encontrado"
    exit 1
fi

# Cargar variables del archivo .env
source .env

# Verificar que las variables requeridas estén definidas
required_vars=("GOOGLE_API_KEY" "FIRECRAWL_API_KEY" "GOOGLE_FACTCHECK_API_KEY" "PERPLEXITY_API_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Error: Las siguientes variables están faltando en .env:"
    printf '%s\n' "${missing_vars[@]}"
    exit 1
fi

echo "✅ Todas las variables requeridas están presentes"

# Actualizar el servicio Cloud Run con todas las variables de entorno
echo "🚀 Actualizando servicio Cloud Run 'factos-agents'..."

gcloud run services update factos-agents \
    --region=us-central1 \
    --set-env-vars="GOOGLE_API_KEY=${GOOGLE_API_KEY},FIRECRAWL_API_KEY=${FIRECRAWL_API_KEY},GOOGLE_FACTCHECK_API_KEY=${GOOGLE_FACTCHECK_API_KEY},PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY},PORT=8080,HOST=0.0.0.0" \
    --quiet

if [ $? -eq 0 ]; then
    echo "✅ Variables de entorno actualizadas exitosamente en Cloud Run"
    echo "🌐 URL del servicio: https://factos-agents-158463493485.us-central1.run.app"
    echo ""
    echo "📋 Variables configuradas:"
    echo "   - GOOGLE_API_KEY: ****${GOOGLE_API_KEY: -4}"
    echo "   - FIRECRAWL_API_KEY: ****${FIRECRAWL_API_KEY: -4}"
    echo "   - GOOGLE_FACTCHECK_API_KEY: ****${GOOGLE_FACTCHECK_API_KEY: -4}"
    echo "   - PERPLEXITY_API_KEY: ****${PERPLEXITY_API_KEY: -4}"
    echo "   - PORT: 8080"
    echo "   - HOST: 0.0.0.0"
else
    echo "❌ Error al actualizar Cloud Run"
    exit 1
fi

echo ""
echo "🔍 Verificando el estado del servicio..."
gcloud run services describe factos-agents --region=us-central1 --format="value(status.conditions[0].status,status.conditions[0].reason)"
