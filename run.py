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

def guardar_periodicamente():
    while True:
        try:
            with open("data.json", "r") as f:
                datos = json.load(f)
            nueva = Registro(
                temperatura=float(datos["temperatura"]),
                humedad=float(datos["humedad"]),
                fecha=datetime.strptime(datos["fecha"], "%Y-%m-%d %H:%M:%S")
            )
            with app.app_context():
                db.session.add(nueva)
                db.session.commit()
            print(f"Guardado: {nueva.temperatura}°C, {nueva.humedad}% at {nueva.fecha}")
        except Exception as e:
            print(f"Error guardando: {e}")
        time.sleep(60)  # Espera 1 minuto

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def data():
    try:
        with open("data.json", "r") as f:
            datos = json.load(f)
        return jsonify(datos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/grafico")
def grafico():
    return render_template("grafico.html")
@app.route("/api/registros")
def api_registros():
    registros = Registro.query.order_by(Registro.fecha.desc()).limit(100).all()
    registros.reverse()  # Para mostrar en orden cronológico

    data = {
        "fechas": [r.fecha.strftime("%H:%M:%S") for r in registros],
        "temperaturas": [r.temperatura for r in registros],
        "humedades": [r.humedad for r in registros]
    }
    return jsonify(data)

@app.route("/registros")
def registros():
    registros = Registro.query.order_by(Registro.fecha.desc()).all()
    return render_template("registros.html", registros=registros)

if __name__ == "__main__":
    # Lanzar thread para guardar datos cada minuto
    thread = threading.Thread(target=guardar_periodicamente, daemon=True)
    thread.start()
    app.run(host="0.0.0.0", port=5000, debug=True)
