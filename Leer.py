import serial 
import time


arduino = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
time.sleep(2)  

try:
    while True:
        line = arduino.readline().decode('utf-8').strip()  # Leer línea y decodificar
        if line:
            partes = line.split(',')
            if len(partes) == 2:
                temperatura, humedad = partes
                print(f"Temperatura: {temperatura} °C | Humedad: {humedad} %")
            else:
                print("Dato inválido:", line)
except KeyboardInterrupt:
    print("\nPrograma asesinado :( ")
finally:
    arduino.close()
