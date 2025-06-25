#!/bin/bash

echo "🚨 LIMPIANDO API KEY EXPUESTA DEL HISTORIAL DE GIT"
echo "=================================================="
echo ""
echo "⚠️  ADVERTENCIA: Esto va a reescribir el historial de git"
echo "    - Los commits cambiarán sus hashes"
echo "    - Necesitarás hacer force push"
echo "    - Todos los colaboradores necesitarán re-clonar"
echo ""

read -p "¿Continuar con la limpieza del historial? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo "❌ Operación cancelada"
    exit 1
fi

# Hacer backup del repositorio
echo "📦 Creando backup del repositorio..."
cp -r . ../factos_agents_backup_$(date +%Y%m%d_%H%M%S)

# Usar git filter-branch para remover la API key del historial
echo "🔧 Removiendo API key del historial..."
git filter-branch --force --index-filter \
    'git rm --cached --ignore-unmatch .env' \
    --prune-empty --tag-name-filter cat -- --all

# Limpiar refs
echo "🧹 Limpiando referencias..."
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo ""
echo "✅ HISTORIAL LIMPIADO"
echo ""
echo "🚀 SIGUIENTES PASOS:"
echo "1. Verificar que .env no esté en el historial:"
echo "   git log --all --full-history -- .env"
echo ""
echo "2. Force push para actualizar el repositorio remoto:"
echo "   git push origin --force --all"
echo ""
echo "3. Notificar a colaboradores que re-clonen el repo"
echo ""
echo "⚠️  Backup creado en: ../factos_agents_backup_*"
