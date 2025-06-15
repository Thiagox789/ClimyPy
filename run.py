from flask import Flask, jsonify, render_template
from models import db, Registro
import json
from datetime import datetime
import threading
import time

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///climypy.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def data():
    try:
        with open("data.json", "r") as f:
            datos = json.load(f)

        # Guardar lectura en la base de datos (solo cuando se pide la ruta /data)
        nueva = Registro(
            temperatura=float(datos["temperatura"]),
            humedad=float(datos["humedad"]),
            fecha=datetime.strptime(datos["fecha"], "%Y-%m-%d %H:%M:%S")
        )
        db.session.add(nueva)
        db.session.commit()

        return jsonify(datos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/api/registros")
def api_registros():
    registros = Registro.query.order_by(Registro.fecha.desc()).limit(100).all()
    resultados = []
    for r in registros:
        resultados.append({
            "id": r.id,
            "temperatura": r.temperatura,
            "humedad": r.humedad,
            "fecha": r.fecha.strftime("%Y-%m-%d %H:%M:%S")
        })
    return jsonify(resultados)

def guardar_datos_periodicamente():
    with app.app_context():
        while True:
            try:
                with open("data.json", "r") as f:
                    datos = json.load(f)

                fecha = datetime.strptime(datos["fecha"], "%Y-%m-%d %H:%M:%S")

                # Evitar duplicados
                existe = Registro.query.filter_by(fecha=fecha).first()
                if not existe:
                    nuevo = Registro(
                        temperatura=datos["temperatura"],
                        humedad=datos["humedad"],
                        fecha=fecha
                    )
                    db.session.add(nuevo)
                    db.session.commit()
                    print("Datos guardados en DB (hilo background)")
                else:
                    print("Dato ya existente, no se guarda")

            except Exception as e:
                print("Error guardando datos:", e)

            time.sleep(60)  # Espera 60 segundos

if __name__ == "__main__":
    # Iniciar hilo que guarda datos cada 60s
    hilo = threading.Thread(target=guardar_datos_periodicamente, daemon=True)
    hilo.start()

    app.run(host="0.0.0.0", port=5000, debug=True)
