#include <WiFiManager.h>      // https://github.com/tzapu/WiFiManager
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

  WiFiManagerParameter custom_server("server", "Server URL (http://ip:puerto/ruta)", serverURL.c_str(), SERVER_URL_MAX_LEN);
  wm.addParameter(&custom_server);

  if (!wm.autoConnect("ESP32-Setup")) {
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
  jsonDoc["chip_temperature"] = chipTemperature;

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
