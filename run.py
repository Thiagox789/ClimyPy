from flask import Flask, jsonify, render_template, request
from models import db, Registro
from datetime import datetime
import pytz

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///climypy.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()

# Zona horaria Argentina
zona_arg = pytz.timezone("America/Argentina/Buenos_Aires")

# Variables globales para almacenar últimos datos
ultimo_dato = {
    "temperatura": 0.0,
    "humedad": 0.0,
    "fecha": datetime.now(zona_arg).strftime("%Y-%m-%d %H:%M:%S")
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/sensor", methods=["POST"])
def recibir_datos():
    try:
        datos = request.get_json()
        
        if not datos or 'temperatura' not in datos or 'humedad' not in datos:
            return jsonify({"error": "Datos incompletos"}), 400
        
        # Actualizar datos globales
        fecha_actual = datetime.now(zona_arg)
        ultimo_dato["temperatura"] = float(datos["temperatura"])
        ultimo_dato["humedad"] = float(datos["humedad"])
        ultimo_dato["fecha"] = fecha_actual.strftime("%Y-%m-%d %H:%M:%S")
        
        # Guardar en base de datos
        nuevo_registro = Registro(
            temperatura=float(datos["temperatura"]),
            humedad=float(datos["humedad"]),
            fecha=fecha_actual
        )
        
        db.session.add(nuevo_registro)
        db.session.commit()
        
        print(f"Datos recibidos: {datos['temperatura']}°C, {datos['humedad']}% - {fecha_actual}")
        
        return jsonify({"status": "success", "message": "Datos guardados correctamente"}), 200
        
    except Exception as e:
        print(f"Error procesando datos: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/data")
def data():
    """Endpoint para obtener los últimos datos (compatibilidad con frontend)"""
    return jsonify(ultimo_dato)

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

@app.route("/status")
def status():
    """Endpoint para verificar el estado del servidor"""
    total_registros = Registro.query.count()
    return jsonify({
        "status": "online",
        "total_registros": total_registros,
        "ultimo_dato": ultimo_dato
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)