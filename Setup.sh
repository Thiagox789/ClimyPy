#!/bin/bash

echo "🔧 Creando entorno virtual..."
python3 -m venv venv || {
    echo "❌ Error: No se pudo crear el entorno virtual. ¿Tenés instalado python3-venv?"
    exit 1
}

echo "✅ Entorno virtual creado."

echo "⚡ Activando entorno virtual..."
source venv/bin/activate || {
    echo "❌ Error al activar el entorno virtual."
    exit 1
}

echo "📦 Instalando dependencias..."
pip install -r requirements.txt || {
    echo "❌ Error instalando dependencias."
    exit 1
}
echo "🌐 Ejecutando servidor Flask..."
python3 run.py

echo "🤖 Ejecutando bot de Telegram..."
#python3 bot_telegram.py
