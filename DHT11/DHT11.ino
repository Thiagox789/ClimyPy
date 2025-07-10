#include <WiFiManager.h>        // https://github.com/tzapu/WiFiManager
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <EEPROM.h>

// ================================
// CONFIGURACIÓN DHT11
// ================================
#define DHT_PIN 4
#define DHT_TYPE DHT11
DHT dht(DHT_PIN, DHT_TYPE);

// PINES
#define BUTTON_PIN 23
#define LED_PIN    22
#define PIEZO_PIN  21

#define BUTTON_PRESS_TIME 3000 // ms

// EEPROM
#define EEPROM_SIZE 512
#define SERVER_URL_ADDR 0
#define SERVER_URL_MAX_LEN 128

// Variables globales
String serverURL = "";

const unsigned long SEND_INTERVAL = 2000;
unsigned long lastSend = 0;

// Variables para el botón
bool buttonPressed = false;
unsigned long buttonPressStart = 0;
bool resetInProgress = false;

// HTML personalizado para el portal
const char* custom_html_head = R"(
<style>
  :root {
  --primary-color: #2a9df4; /* azul para botones y highlights */
  --secondary-color: #a0a0a0; /* gris para subtítulos y texto menos importante */
  --background: #fafafa; /* fondo muy claro */
  --text-color: #333333; /* texto principal oscuro pero no negro */
  --border-color: #ddd; /* borde sutil */
  --border-radius: 6px;
  --shadow: 0 2px 6px rgba(0, 0, 0, 0.07);
  --font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

body {
  background: var(--background);
  color: var(--text-color);
  font-family: var(--font-family);
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  margin: 0;
  padding: 20px;
}

.container {
  background: white;
  padding: 30px 40px;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow);
  max-width: 400px;
  width: 100%;
  animation: fadeIn 0.4s ease-out;
}

.header {
  text-align: center;
  margin-bottom: 25px;
}

.logo {
  font-size: 2.8rem;
  margin-bottom: 10px;
  color: var(--primary-color);
}

.title {
  font-size: 1.8rem;
  font-weight: 600;
  margin-bottom: 5px;
}

.subtitle {
  font-size: 1rem;
  color: var(--secondary-color);
  font-weight: 400;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
}

input[type="text"], input[type="password"], select {
  width: 100%;
  padding: 10px 14px;
  border: 1.5px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: 1rem;
  transition: border-color 0.3s ease;
  outline: none;
}

input[type="text"]:focus, input[type="password"]:focus, select:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 6px rgba(42, 157, 244, 0.4);
}

.btn {
  width: 100%;
  padding: 12px 0;
  border: none;
  border-radius: var(--border-radius);
  background: var(--primary-color);
  color: white;
  font-weight: 700;
  font-size: 1.1rem;
  cursor: pointer;
  transition: background-color 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.6px;
}

.btn:hover {
  background: #2380d9;
}

.info-card {
  background: #f9f9f9;
  border-left: 4px solid var(--primary-color);
  padding: 16px 20px;
  margin-bottom: 20px;
  border-radius: var(--border-radius);
  color: var(--secondary-color);
  font-size: 0.9rem;
  line-height: 1.4;
}

.status-indicator {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 8px;
  vertical-align: middle;
}

.status-online {
  background: #4caf50;
  animation: pulse 2s infinite;
}

.status-offline {
  background: #f44336;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.footer {
  text-align: center;
  font-size: 0.8rem;
  color: var(--secondary-color);
  margin-top: 25px;
  padding-top: 15px;
  border-top: 1px solid var(--border-color);
}

@media (max-width: 500px) {
  .container {
    padding: 20px;
    margin: 10px;
  }
  
  .title {
    font-size: 1.5rem;
  }
}
</style>
)";

const char* custom_html_body = R"(
<div class="container">
  <div class="header">
    <div class="logo">🌡️</div>
    <h1 class="title">ClimyPy Station</h1>
    <p class="subtitle">Configuración de Monitoreo Climático</p>
  </div>
  
  <div class="info-card">
    <h3>📡 Estado de Conexión</h3>
    <p><span class="status-indicator status-online"></span>Listo para configurar</p>
    <p>Complete los campos siguientes para conectar su estación climática.</p>
  </div>
)";

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println();
  Serial.println(F("🚀 ESP32 - ClimyPy Arrancando..."));

  // Configurar pines
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  pinMode(PIEZO_PIN, OUTPUT);

  // Apagar LED y piezo al inicio
  digitalWrite(LED_PIN, LOW);
  noTone(PIEZO_PIN);

  // Chequear si el botón está presionado al inicio
  checkButtonAtStartup();

  dht.begin();

  EEPROM.begin(EEPROM_SIZE);

  serverURL = readServerURLFromEEPROM();
  Serial.print("➡ Server URL almacenada: ");
  Serial.println(serverURL);

  WiFiManager wm;
  
  // Configurar HTML personalizado
  wm.setCustomHeadElement(custom_html_head);
  
  // =========================================================
  // MODIFICACIÓN: La siguiente línea fue eliminada porque
  // causaba el error de compilación.
  // wm.setCustomBodyElement(custom_html_body);
  // =========================================================
  
  // Configurar textos personalizados
  wm.setTitle("ClimyPy Station");
  wm.setDarkMode(false); // Aunque usemos colores oscuros, este flag controla el tema interno de WiFiManager, no el CSS
  
  // =========================================================
  // MODIFICACIÓN: El HTML del cuerpo ahora se añade como un
  // parámetro personalizado para que se muestre en la página.
  // =========================================================
  WiFiManagerParameter custom_header(custom_html_body);
  WiFiManagerParameter custom_server("server", "🌐 URL del Servidor", serverURL.c_str(), SERVER_URL_MAX_LEN, "placeholder=\"http://192.168.1.90:5000/api/sensor\" style=\"margin-bottom: 10px;\"");
  WiFiManagerParameter custom_info("<div class=\"info-card\"><h3>📋 Instrucciones</h3><p>1. Selecciona tu red WiFi<br>2. Introduce la contraseña<br>3. Configura la URL del servidor donde se enviarán los datos<br>4. Haz clic en 'Guardar' para completar la configuración</p></div>");
  
  // Añadir parámetros
  wm.addParameter(&custom_header); // <-- Encabezado añadido aquí
  wm.addParameter(&custom_info);
  wm.addParameter(&custom_server);

  // Configurar timeout más largo para dar tiempo a configurar
  wm.setConfigPortalTimeout(300); // 5 minutos
  
  // Mensaje de configuración personalizado
  wm.setAPCallback([](WiFiManager *myWiFiManager) {
    Serial.println("🎯 Portal de configuración iniciado");
    Serial.print("📱 Conéctate a la red: ");
    Serial.println(myWiFiManager->getConfigPortalSSID());
    Serial.println("🌐 Ve a: http://192.168.4.1");
    Serial.println("⏰ Tiempo límite: 5 minutos");
    
    // Indicador visual de que está en modo configuración
    for (int i = 0; i < 3; i++) {
      digitalWrite(LED_PIN, HIGH);
      tone(PIEZO_PIN, 1000, 200);
      delay(200);
      digitalWrite(LED_PIN, LOW);
      noTone(PIEZO_PIN);
      delay(200);
    }
  });

  // Personalizar el botón de guardar
  wm.setSaveConfigCallback([]() {
    Serial.println("✅ Configuración guardada exitosamente!");
    
    // Señal de éxito
    for (int i = 0; i < 5; i++) {
      digitalWrite(LED_PIN, HIGH);
      tone(PIEZO_PIN, 2000, 100);
      delay(100);
      digitalWrite(LED_PIN, LOW);
      noTone(PIEZO_PIN);
      delay(100);
    }
  });

  if (!wm.autoConnect("ClimyPy-Setup")) {
    Serial.println("❌ No se pudo conectar a WiFi. Reiniciando...");
    delay(3000);
    ESP.restart();
  }

  Serial.println("✅ WiFi conectado!");
  Serial.print("IP Local: ");
  Serial.println(WiFi.localIP());

  String newServerURL = custom_server.getValue();
  if (newServerURL.length() > 0 && newServerURL != serverURL) {
    Serial.println("ℹ️ Guardando nueva Server URL en EEPROM...");
    writeServerURLToEEPROM(newServerURL);
    serverURL = newServerURL;
  }
  
  // Señal de conexión exitosa
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, HIGH);
    tone(PIEZO_PIN, 1500, 300);
    delay(300);
    digitalWrite(LED_PIN, LOW);
    noTone(PIEZO_PIN);
    delay(200);
  }
}

void loop() {
  unsigned long currentTime = millis();

  // Verificar estado del botón continuamente
  checkButtonPress();

  if (currentTime - lastSend >= SEND_INTERVAL) {
    sendSensorData();
    lastSend = currentTime;
  }

  delay(100); // Reducir delay para mejor respuesta del botón
}

void checkButtonAtStartup() {
  // Verificar si el botón está presionado al inicio
  if (digitalRead(BUTTON_PIN) == LOW) {
    Serial.println("🔴 BOTÓN presionado al inicio. Esperando confirmación...");
    
    unsigned long pressedTime = millis();
    bool ledState = false;
    unsigned long lastBlink = 0;
    
    while (digitalRead(BUTTON_PIN) == LOW) {
      // Parpadear LED y hacer beep intermitente
      if (millis() - lastBlink >= 200) {
        ledState = !ledState;
        digitalWrite(LED_PIN, ledState);
        if (ledState) {
          tone(PIEZO_PIN, 2000, 100);
        }
        lastBlink = millis();
      }

      if (millis() - pressedTime >= BUTTON_PRESS_TIME) {
        Serial.println("⚠️ Mantuvimos presionado suficiente tiempo. Reseteando configuración...");
        
        // Señal de confirmación
        for (int i = 0; i < 3; i++) {
          digitalWrite(LED_PIN, HIGH);
          tone(PIEZO_PIN, 3000, 300);
          delay(300);
          digitalWrite(LED_PIN, LOW);
          noTone(PIEZO_PIN);
          delay(200);
        }
        
        // Borrar WiFiManager
        WiFiManager wm;
        wm.resetSettings();

        // Borrar URL del servidor en EEPROM
        clearServerURLInEEPROM();

        Serial.println("✅ Configuración borrada. Reiniciando ESP...");
        delay(2000);
        ESP.restart();
      }
    }
    
    // Si soltás antes del tiempo:
    Serial.println("✅ Botón soltado antes de tiempo. No se borra nada.");
    digitalWrite(LED_PIN, LOW);
    noTone(PIEZO_PIN);
  }
}

void checkButtonPress() {
  bool currentButtonState = (digitalRead(BUTTON_PIN) == LOW);
  
  if (currentButtonState && !buttonPressed) {
    // Botón recién presionado
    buttonPressed = true;
    buttonPressStart = millis();
    resetInProgress = false;
    Serial.println("🔴 Botón presionado...");
  }
  
  if (buttonPressed && currentButtonState) {
    // Botón sigue presionado
    unsigned long pressedDuration = millis() - buttonPressStart;
    
    if (pressedDuration >= BUTTON_PRESS_TIME && !resetInProgress) {
      // Tiempo suficiente alcanzado
      resetInProgress = true;
      Serial.println("⚠️ Tiempo suficiente alcanzado. Reseteando configuración...");
      
      // Señal de confirmación
      for (int i = 0; i < 5; i++) {
        digitalWrite(LED_PIN, HIGH);
        tone(PIEZO_PIN, 3000, 200);
        delay(200);
        digitalWrite(LED_PIN, LOW);
        noTone(PIEZO_PIN);
        delay(100);
      }
      
      // Borrar configuración
      WiFiManager wm;
      wm.resetSettings();
      clearServerURLInEEPROM();
      
      Serial.println("✅ Configuración borrada. Reiniciando ESP...");
      delay(2000);
      ESP.restart();
    }
    
    // Indicador visual mientras se presiona
    if (pressedDuration < BUTTON_PRESS_TIME) {
      // Parpadear LED más rápido conforme se acerca al tiempo
      int blinkInterval = map(pressedDuration, 0, BUTTON_PRESS_TIME, 500, 100);
      static unsigned long lastBlink = 0;
      static bool ledState = false;
      
      if (millis() - lastBlink >= blinkInterval) {
        ledState = !ledState;
        digitalWrite(LED_PIN, ledState);
        if (ledState) {
          tone(PIEZO_PIN, 2000, 50);
        }
        lastBlink = millis();
      }
    }
  }
  
  if (!currentButtonState && buttonPressed) {
    // Botón soltado
    buttonPressed = false;
    resetInProgress = false;
    digitalWrite(LED_PIN, LOW);
    noTone(PIEZO_PIN);
    Serial.println("✅ Botón soltado.");
  }
}

void sendSensorData() {
  if (serverURL.length() == 0) {
    Serial.println("⚠️ No se configuró ninguna Server URL. No se envían datos.");
    return;
  }

  float temperaturaDHT = dht.readTemperature();
  float humedadDHT = dht.readHumidity();
  float chipTemperature = temperatureRead();

  if (isnan(temperaturaDHT) || isnan(humedadDHT)) {
    Serial.println("⚠️ Error leyendo sensor DHT11.");
    return;
  }

  StaticJsonDocument<256> jsonDoc;
  jsonDoc["temperatura"] = temperaturaDHT;
  jsonDoc["humedad"] = humedadDHT;
  jsonDoc["temperatura_interna_esp"] = chipTemperature;
  
  String jsonString;
  serializeJson(jsonDoc, jsonString);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(5000);

    int httpResponseCode = http.POST(jsonString);

    if (httpResponseCode == 200 || httpResponseCode == 201) {
      Serial.println("✅ Datos enviados exitosamente!");
      Serial.printf("→ Temp DHT11: %.2f°C\n", temperaturaDHT);
      Serial.printf("→ Humedad DHT11: %.2f%%\n", humedadDHT);
      Serial.printf("→ Temp Chip ESP32: %.2f°C\n", chipTemperature);

      String response = http.getString();
      Serial.println("Respuesta del servidor:");
      Serial.println(response);
    } else {
      Serial.print("❌ Error en petición HTTP: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  } else {
    Serial.println("⚠️ WiFi desconectado. No se pudo enviar datos.");
  }
}

String readServerURLFromEEPROM() {
  String url = "";
  for (int i = 0; i < SERVER_URL_MAX_LEN; i++) {
    char c = EEPROM.read(SERVER_URL_ADDR + i);
    if (c == 0xFF || c == '\0') break;
    url += c;
  }
  return url;
}

void writeServerURLToEEPROM(String url) {
  int len = url.length();
  for (int i = 0; i < SERVER_URL_MAX_LEN; i++) {
    if (i < len) {
      EEPROM.write(SERVER_URL_ADDR + i, url[i]);
    } else {
      EEPROM.write(SERVER_URL_ADDR + i, '\0');
    }
  }
  EEPROM.commit();
  Serial.println("✅ URL guardada en EEPROM.");
}

void clearServerURLInEEPROM() {
  for (int i = 0; i < SERVER_URL_MAX_LEN; i++) {
    EEPROM.write(SERVER_URL_ADDR + i, '\0');
  }
  EEPROM.commit();
  Serial.println("✅ URL del servidor borrada de EEPROM.");
}
