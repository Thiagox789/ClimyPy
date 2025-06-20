# ClimyPy

ClimyPy es un proyecto diseñado para monitorear la temperatura y la humedad utilizando un sensor **DHT11** conectado a una placa Arduino. Los datos se procesan y almacenan en una base de datos, y se presentan en una interfaz web interactiva.

## 🚀 Características

- **Lectura de datos en tiempo real** desde el sensor DHT11 mediante conexión USB Serial.
- **Visualización en tiempo real** de temperatura y humedad en una interfaz web moderna.
- **Gráficos históricos** para analizar tendencias de temperatura y humedad.
- **Almacenamiento automático** de registros en una base de datos SQLite.
- **API REST** para acceder a los datos históricos.

## ✅ Objetivos

1. Configurar el sensor DHT11 en Arduino para enviar datos por el puerto serial.
2. Crear un programa en Python para leer los datos del puerto serial y almacenarlos.
3. Desarrollar una interfaz web con Flask para mostrar los datos en tiempo real y gráficos históricos.
4. Documentar el proceso de configuración y uso del proyecto.

## 📂 Estructura del Proyecto

```bash
ClimyPy/
│
├── arduino/                  # Código y configuraciones para Arduino
│   ├── DHT11_sensor.ino      # Sketch de Arduino para el sensor DHT11
│   └── ...
│
├── python/                   # Scripts en Python para procesamiento de datos
│   ├── serial_listener.py    # Script para leer datos del puerto serial
│   ├── database_handler.py   # Manejo de la base de datos SQLite
│   └── ...
│
├── web/                      # Archivos para la interfaz web
│   ├── app.py                # Aplicación principal de Flask
│   ├── templates/            # Plantillas HTML
│   └── static/               # Archivos estáticos (CSS, JS, imágenes)
│
├── requirements.txt          # Dependencias del proyecto
└── README.md                 # Documentación del proyecto
```

## 🛠️ Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/tu-usuario/ClimyPy.git
   cd ClimyPy
   ```

2. **Ejecutar el script de configuración**:
   ```bash
   chmod +x Setup.sh
   ./Setup.sh
   ```

## 🌐 Uso

- Accede a la interfaz web en [http://localhost:5000] o [http://ip_server:5000]
- Visualiza los gráficos históricos en [http://localhost:5000/grafico] o [http://ip_server:5000/grafico]
- Consulta los registros en [http://localhost:5000/registros] o [http://ip_server:5000/registros]

## 📦 Dependencias

Las dependencias del proyecto están listadas en `requirements.txt`. Instálalas con:
```bash
pip install -r requirements.txt
```

