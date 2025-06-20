import serial
import time
import json
from datetime import datetime
import pytz

arduino = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
time.sleep(2)

zona_arg = pytz.timezone("America/Argentina/Buenos_Aires")
fecha_actual = datetime.now(zona_arg).strftime("%Y-%m-%d %H:%M:%S")

try:
    while True:
        line = arduino.readline().decode('utf-8').strip()
        if line:
            partes = line.split(',')
            if len(partes) == 2:
                temperatura, humedad = partes
                fecha_actual = datetime.now(zona_arg).strftime("%Y-%m-%d %H:%M:%S")
                datos = {
                    "temperatura": float(temperatura),
                    "humedad": float(humedad),
                    "fecha": fecha_actual
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
