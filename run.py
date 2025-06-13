from flask import Flask, jsonify, render_template
from models import db, Registro
import json
from datetime import datetime

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

        # Guardar lectura en la base de datos
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
