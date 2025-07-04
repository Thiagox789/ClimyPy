# ClimyPy ESP32 🌡️

ClimyPy es un sistema de monitoreo de temperatura y humedad que utiliza un **ESP32** con sensor **DHT11** para enviar datos via **WiFi** a un servidor Flask.

## 🚀 Características

- **ESP32 con WiFi**: Envío inalámbrico de datos cada 30 segundos
- **Sensor DHT11**: Lectura precisa de temperatura y humedad
- **Interfaz web moderna**: Visualización en tiempo real y gráficos históricos
- **Base de datos SQLite**: Almacenamiento automático de todos los registros
- **API REST**: Endpoints para recibir y consultar datos

## 📂 Estructura del Proyecto

```
ClimyPy-ESP32/
├── sensor_esp32.ino          # Código para ESP32
├── run.py                    # Servidor Flask
├── models.py                 # Modelo de base de datos
├── requirements.txt          # Dependencias Python
├── Setup.sh                  # Script de instalación
├── templates/
│   ├── index.html           # Dashboard principal
│   ├── grafico.html         # Gráficos históricos
│   └── registros.html       # Tabla de registros
└── static/
    ├── css/styles.css       # Estilos
    └── js/app.js            # JavaScript frontend
```

## 🛠️ Instalación

### 1. Configurar el servidor Python

```bash
# Clonar y configurar
git clone https://github.com/tu-usuario/ClimyPy-ESP32.git
cd ClimyPy-ESP32

# Ejecutar script de configuración
chmod +x Setup.sh
./Setup.sh
```

### 2. Configurar ESP32

1. **Instalar librerías en Arduino IDE:**
   - WiFi (incluida en ESP32)
   - HTTPClient (incluida en ESP32)
   - ArduinoJson (buscar en Library Manager)
   - DHT sensor library (buscar "DHT" por Adafruit)

2. **Modificar configuración WiFi en `sensor_esp32.ino`:**
   ```cpp
   const char* ssid = "TU_WIFI";
   const char* password = "TU_PASSWORD";
   const char* serverURL = "http://IP_DEL_SERVIDOR:5000/api/sensor";
   ```

3. **Conexión DHT11:**
   - VCC → 3.3V
   - GND → GND
   - DATA → GPIO 4

### 3. Ejecutar el sistema

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar servidor
python3 run.py
```

## 🌐 Uso

- **Dashboard principal**: `http://localhost:5000`
- **Gráficos históricos**: `http://localhost:5000/grafico`
- **Registros**: `http://localhost:5000/registros`
- **Estado del sistema**: `http://localhost:5000/status`

## 🔧 API Endpoints

- `POST /api/sensor` - Recibe datos del ESP32
- `GET /data` - Obtiene últimos datos
- `GET /api/registros` - Datos para gráficos
- `GET /status` - Estado del sistema

## 📡 Flujo de datos

1. ESP32 lee sensor DHT11 cada 30 segundos
2. Envía datos JSON via HTTP POST al servidor Flask
3. Flask almacena datos en SQLite y actualiza cache
4. Interfaz web muestra datos en tiempo real

## 🐛 Troubleshooting

- **ESP32 no conecta**: Verificar credenciales WiFi
- **Error HTTP**: Comprobar IP del servidor
- **Sin datos**: Verificar conexión del sensor DHT11
- **Servidor no responde**: Verificar que Flask esté ejecutándose

## 📦 Dependencias

- **ESP32**: WiFi, HTTPClient, ArduinoJson, DHT
- **Python**: Flask, SQLAlchemy, pytz