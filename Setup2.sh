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

echo "📦 Instalando dependencias principales desde requirements.txt..."
pip install -r requirements.txt || {
    echo "❌ Error instalando dependencias principales."
    exit 1
}

# --- Importante: Instalar las dependencias del bot si no están en requirements.txt ---
# Si python-telegram-bot y requests YA están en tu requirements.txt, esta línea es redundante pero segura.
echo "🤖 Asegurando que las dependencias del bot de Telegram estén instaladas..."
pip install python-telegram-bot requests || {
    echo "❌ Error instalando dependencias del bot de Telegram."
    exit 1
}
echo "✅ Dependencias del bot instaladas."

echo "🌐 Ejecutando servidor Flask en segundo plano..."
# Ejecuta run.py en segundo plano.
# 'nohup' permite que el proceso continúe incluso si cierras la terminal.
# ' > flask_output.log 2>&1' redirige la salida de Flask a un archivo de log.
# El '&' al final envía el comando a segundo plano.
nohup python3 run.py > flask_output.log 2>&1 &

# Guarda el ID del proceso de Flask para poder detenerlo más tarde
FLASK_PID=$!
echo "✅ Servidor Flask iniciado en segundo plano. PID: $FLASK_PID. Puedes ver sus logs en 'flask_output.log'"

echo "🤖 Ejecutando bot de Telegram en primer plano..."
# Asegúrate de que tu bot_telegram.py tenga el TELEGRAM_BOT_TOKEN
# y FLASK_APP_BASE_URL configurados correctamente (http://192.168.100.90:5000 o tu IP/dominio).
python3 bot_telegram.py

echo "Script de inicio finalizado."
echo "Para detener el servidor Flask que se está ejecutando en segundo plano, usa el siguiente comando:"
echo "kill $FLASK_PID"
echo "Puedes revisar el log de Flask en: cat flask_output.log"
