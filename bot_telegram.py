import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import os
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode

# Configura el logging (opcional, pero recomendado para depuración)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Reemplaza 'TU_BOT_TOKEN' con el token que te dio BotFather
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7839645181:AAE8D8QlEfccceNpX1kGJXzkBYA5ut4UrxU")

# URL de tu aplicación Flask (asegúrate de que sea accesible desde donde corres el bot)
# Si lo estás probando localmente, y el bot y Flask corren en la misma máquina, usa localhost.
# Si tu Flask está desplegado, usa la URL pública.
FLASK_APP_BASE_URL = os.getenv("FLASK_APP_BASE_URL", "http://192.168.100.90:5000") # o tu_dominio.com

# --- Handlers para los comandos del bot ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envía un mensaje de bienvenida cuando se ejecuta el comando /start."""
    user = update.effective_user
    # Para el mensaje de bienvenida, usamos HTML que es más flexible con los caracteres.
    await update.message.reply_html(
        f"¡Hola {user.mention_html()}!\n"
        "Soy el bot de ClimyPy. Puedes consultarme los datos actuales:\n"
        "/temperatura - Obtiene la última temperatura\n"
        "/humedad - Obtiene la última humedad\n"
        "/datos - Obtiene temperatura y humedad a la vez\n"
        "/estadisticas - Obtiene estadísticas del sistema\n"
    )

async def get_current_data(command: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Función auxiliar para obtener y enviar datos."""
    try:
        response = requests.get(f"{FLASK_APP_BASE_URL}/data")
        response.raise_for_status() # Lanza un error para códigos de estado HTTP 4xx/5xx
        data = response.json()

        # Escapar los valores que pueden contener caracteres especiales para MarkdownV2
        # Convertimos a string primero por si el valor es numérico o None
        temperatura_val = escape_markdown(str(data.get('temperatura', '--')), version=2)
        humedad_val = escape_markdown(str(data.get('humedad', '--')), version=2)
        fecha_val = escape_markdown(str(data.get('fecha', '--')), version=2)

        # Los asteriscos para negrita (*) están bien en MarkdownV2. El problema eran los puntos en los valores.
        if command == "temperatura":
            message = (
                f"🌡️ *Temperatura actual:* {temperatura_val}°C\n"
                f"Última actualización: {fecha_val}"
            )
        elif command == "humedad":
            message = (
                f"💧 *Humedad actual:* {humedad_val}%\n"
                f"Última actualización: {fecha_val}"
            )
        else: # command == "datos"
            message = (
                f"🌡️ *Temperatura:* {temperatura_val}°C\n"
                f"💧 *Humedad:* {humedad_val}%\n"
                f"Última actualización: {fecha_val}"
            )

        # Usar reply_text con parse_mode
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error al conectar con la aplicación Flask: {e}")
        await update.message.reply_text("Lo siento, no pude conectar con la aplicación ClimyPy para obtener los datos.")
    except Exception as e:
        logger.error(f"Error inesperado al obtener datos: {e}")
        await update.message.reply_text("Ocurrió un error al procesar tu solicitud.")

async def temperatura(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /temperatura."""
    await get_current_data("temperatura", update, context)

async def humedad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /humedad."""
    await get_current_data("humedad", update, context)

async def datos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /datos."""
    await get_current_data("datos", update, context)

async def estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /estadisticas."""
    try:
        # CORRECCIÓN: La ruta correcta en Flask es /status, no /stats
        response = requests.get(f"{FLASK_APP_BASE_URL}/status")
        response.raise_for_status()
        data = response.json()

        # Los valores dentro de las comillas invertidas (backticks `) en MarkdownV2
        # son tratados como bloques de código y no necesitan ser escapados.
        # Las barras invertidas para escapar el punto y los paréntesis en el texto fijo están bien.
        total_records_val = data.get('total_records', '--')
        uptime_val = data.get('uptime', '--')
        avg_temp_val = data.get('average_temperature_last_24h', '--')
        avg_hum_val = data.get('average_humidity_last_24h', '--')

        message = (
            f"📊 *Estadísticas del Sistema ClimyPy:*\n"
            f"  • Total de Registros: `{total_records_val}`\n"
            f"  • Tiempo de actividad: `{uptime_val}`\n"
            f"  • Temp\\. Promedio \\(24h\\): `{avg_temp_val}`°C\n"
            f"  • Hum\\. Promedio \\(24h\): `{avg_hum_val}`%"
        )
        # Usar reply_text con parse_mode
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error al conectar con la aplicación Flask para estadísticas: {e}")
        await update.message.reply_text("Lo siento, no pude conectar con la aplicación ClimyPy para obtener las estadísticas.")
    except Exception as e:
        logger.error(f"Error inesperado al obtener estadísticas: {e}")
        await update.message.reply_text("Ocurrió un error al procesar tu solicitud de estadísticas.")

def main() -> None:
    """Inicia el bot."""
    # Crea la aplicación y pásale el token de tu bot.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Añade los handlers para los comandos.
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("temperatura", temperatura))
    application.add_handler(CommandHandler("humedad", humedad))
    application.add_handler(CommandHandler("datos", datos))
    application.add_handler(CommandHandler("estadisticas", estadisticas))

    # Inicia el bot (bloquea la ejecución hasta que se detenga con Ctrl+C)
    logger.info("Bot de Telegram iniciado. Presiona Ctrl+C para detenerlo.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
