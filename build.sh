#!/usr/bin/env bash
# Build script para Render.com
# Este script se ejecuta automáticamente durante el despliegue

# Salir inmediatamente si un comando falla
set -o errexit

echo "=========================================="
echo "Iniciando build del Planificador de Horarios"
echo "=========================================="

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# Crear directorios necesarios si no existen
echo "📁 Creando directorios necesarios..."
mkdir -p logs
mkdir -p mediafiles
mkdir -p staticfiles

# Recopilar archivos estáticos
echo "🎨 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# Aplicar migraciones de base de datos
echo "🗄️ Aplicando migraciones..."
python manage.py migrate

echo "=========================================="
echo "✅ Build completado exitosamente"
echo "=========================================="
