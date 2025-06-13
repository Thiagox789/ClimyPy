import serial
import time
import json

arduino = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
time.sleep(2)

try:
    while True:
        line = arduino.readline().decode('utf-8').strip()
        if line:
            partes = line.split(',')
            if len(partes) == 2:
                temperatura, humedad = partes
                datos = {
                    "temperatura": float(temperatura),
                    "humedad": float(humedad),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                with open("data.json", "w") as archivo:
                    json.dump(datos, archivo)
                print(f"Guardado: {datos}")
            else:
                print("Dato inválido:", line)
except KeyboardInterrupt:
    print("\nPrograma asesinado :( ")
finally:
    arduino.close()
