#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

// Configuración WiFi
const char* ssid = "TU_WIFI";
const char* password = "TU_PASSWORD";

// Configuración servidor
const char* serverURL = "http://192.168.1.100:5000/api/sensor";

// Configuración DHT11
#define DHT_PIN 4
#define DHT_TYPE DHT11
DHT dht(DHT_PIN, DHT_TYPE);

// Intervalo de envío (30 segundos)
const unsigned long SEND_INTERVAL = 30000;
unsigned long lastSend = 0;

void setup() {
  Serial.begin(115200);
  dht.begin();
  
  // Conectar a WiFi
  WiFi.begin(ssid, password);
  Serial.print("Conectando a WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.println("WiFi conectado!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  unsigned long currentTime = millis();
  
  if (currentTime - lastSend >= SEND_INTERVAL) {
    sendSensorData();
    lastSend = currentTime;
  }
  
  delay(1000);
}

void sendSensorData() {
  float temperatura = dht.readTemperature();
  float humedad = dht.readHumidity();
  
  // Verificar si las lecturas son válidas
  if (isnan(temperatura) || isnan(humedad)) {
    Serial.println("Error leyendo sensor DHT11");
    return;
  }
  
  // Crear JSON
  StaticJsonDocument<200> jsonDoc;
  jsonDoc["temperatura"] = temperatura;
  jsonDoc["humedad"] = humedad;
  
  String jsonString;
  serializeJson(jsonDoc, jsonString);
  
  // Enviar datos
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");
    
    int httpResponseCode = http.POST(jsonString);
    
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Datos enviados exitosamente");
      Serial.printf("Temperatura: %.2f°C, Humedad: %.2f%%\n", temperatura, humedad);
    } else {
      Serial.print("Error en petición HTTP: ");
      Serial.println(httpResponseCode);
    }
    
    http.end();
  } else {
    Serial.println("WiFi desconectado");
  }
}
