from flask import Flask, jsonify, render_template_string
import json

app = Flask(__name__)

@app.route("/")
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ClimyPy</title>
        <meta charset="UTF-8">
    </head>
    <body>
        <h1>Datos en vivo 🌡️💧</h1>
        <p>Temperatura: <span id="temp">--</span> °C</p>
        <p>Humedad: <span id="hum">--</span> %</p>
        <p>Actualizado: <span id="time">--</span></p>

        <script>
            function actualizarDatos() {
                fetch("/data")
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById("temp").textContent = data.temperatura;
                        document.getElementById("hum").textContent = data.humedad;
                        document.getElementById("time").textContent = data.timestamp;
                    })
                    .catch(error => console.log("Error:", error));
            }

            setInterval(actualizarDatos, 2000); // cada 2 segundos
            actualizarDatos(); // llamada inicial
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

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

