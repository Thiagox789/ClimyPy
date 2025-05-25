#include <DHT.h>

#define DHTPIN 2
#define DHTYPE DHT11   

DHT dht(DHTPIN,DHTYPE);

void setup() 
{
    Serial.begin(9600); //no me acurdo que hacia pero habia que ponerlo 
    dht.begin(); 
}

void loop() {
  float humedad = dht.readHumidity(); //Definir la variable humedad de tipo flotante :c
  float temperatura = dht.readTemperature(); //Definir la variable temperatura de tipo flotante :c

  if (isnan(humedad) || isnan(temperatura)) {
    Serial.println("Error al leer el sensor");
    return;
  }

 // Serial.print("Temperatura: "); //Printea Temperatura
  Serial.print(temperatura);     //Printea la variable temperatura :) 
  //Serial.print(" °C, Humedad: ");//Printea la unidad de temperatura y ademas printea Humedad
  Serial.print(",");            //Printea una simple coma ;v 
  Serial.println(humedad);        //Printea la variable humedad :) 
  //Serial.println(" %");         //Printea la unidad de humedad 
  delay(2000); 
}

