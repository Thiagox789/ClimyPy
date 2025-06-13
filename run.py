from flask import Flask, jsonify, render_template
import json

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/data")
def data():
    try:
        with open("data.json", "r") as f:
            datos = json.load(f)
        return jsonify(datos)
    except FileNotFoundError:
        return jsonify({"error": "No hay datos disponibles"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

