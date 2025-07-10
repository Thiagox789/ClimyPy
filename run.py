# run.py - VERSIÓN FINAL Y COMPLETA

from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
from models import db, Registro, User
from datetime import datetime, timedelta
import os
import pytz
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from forms import RegistrationForm, LoginForm

app = Flask(__name__)
# Configuración de la base de datos SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///climypy.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
db.init_app(app)

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Creación de tablas y usuario admin
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', email='admin@climypy.com', is_admin=True)
        admin_user.set_password('lobito200')
        db.session.add(admin_user)
        db.session.commit()
        print("Usuario 'admin' creado con contraseña 'lobito200' y email 'admin@climypy.com'.")

# Zona horaria
zona_arg = pytz.timezone("America/Argentina/Buenos_Aires")

# --- CAMBIO 1: Variable global inicializada en None ---
# Esto nos permite saber si alguna vez hemos recibido datos del sensor.
ultimo_dato = {
    "temperatura": None,
    "humedad": None,
    "fecha": None,
    "temperatura_interna_esp": None # Nuevo: Temperatura interna del chip
}

# --- Rutas para la interfaz web (sin cambios) ---
@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('¡Tu cuenta ha sido creada! Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Registro', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Inicio de sesión fallido. Verifica tus credenciales.', 'danger')
    return render_template('login.html', title='Iniciar Sesión', form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/grafico")
@login_required
def grafico():
    return render_template("grafico.html")

@app.route("/registros")
@login_required
def registros():
    registros = Registro.query.order_by(Registro.fecha.desc()).all()
    return render_template("registros.html", registros=registros)

# --- Ruta API para el sensor (sin cambios) ---
# Esta ruta actualiza la variable `ultimo_dato`
@app.route("/api/sensor", methods=["POST"])
def recibir_datos():
    try:
        datos = request.get_json()
        if not datos or 'temperatura' not in datos or 'humedad' not in datos:
            return jsonify({"error": "Datos incompletos"}), 400

        fecha_actual = datetime.now(zona_arg).strftime("%Y-%m-%d %H:%M:%S")
        
        # Actualizamos el diccionario en memoria con todos los datos que llegan
        ultimo_dato["temperatura"] = float(datos["temperatura"])
        ultimo_dato["humedad"] = float(datos["humedad"])
        # Guardamos la temperatura del chip ESP32 solo en memoria, si es que viene
        ultimo_dato["temperatura_interna_esp"] = datos.get("temperatura_interna_esp")
        ultimo_dato["fecha"] = fecha_actual

        # A la base de datos solo guardamos la temperatura y humedad del sensor DHT11
        nuevo_registro = Registro(
            temperatura=float(datos["temperatura"]),
            humedad=float(datos["humedad"]),
            fecha=datetime.now(zona_arg)
        )
        db.session.add(nuevo_registro)
        db.session.commit()

        temp_interna_str = f", Temp. ESP: {ultimo_dato['temperatura_interna_esp']}°C" if ultimo_dato.get('temperatura_interna_esp') is not None else ""
        print(f"[{fecha_actual}] Datos recibidos: Temp: {datos['temperatura']}°C, Hum: {datos['humedad']}%{temp_interna_str}")
        return jsonify({"status": "success", "message": "Datos guardados"}), 200

    except Exception as e:
        print(f"Error procesando datos: {e}")
        return jsonify({"error": str(e)}), 500

# --- CAMBIO 2: Ruta /data con la lógica de estado ---
# Esta es la ruta que consume tu app de Flutter.
@app.route("/data")
@login_required
def data():
    """Endpoint para obtener los últimos datos con estado de conexión del sensor."""
    # Si no hemos recibido datos en 15 segundos, se considera offline.
    # Puedes ajustar este valor.
    SENSOR_TIMEOUT_SECONDS = 15

    # Caso 1: El servidor acaba de iniciar y nunca ha recibido datos.
    if ultimo_dato.get("fecha") is None:
        return jsonify({
            "status": "offline",
            "temperatura": 0.0, # Devolvemos 0.0 para no romper la UI de la app
            "humedad": 0.0,
            "temperatura_interna_esp": 0.0,
            "fecha": "Aguardando datos del sensor..."
        })

    try:
        # Caso 2: Ya hemos recibido datos, comprobamos si son recientes.
        fecha_ultimo_dato = datetime.strptime(ultimo_dato["fecha"], "%Y-%m-%d %H:%M:%S")
        fecha_ultimo_dato = zona_arg.localize(fecha_ultimo_dato)
        ahora = datetime.now(zona_arg)
        diferencia = ahora - fecha_ultimo_dato

        response_data = ultimo_dato.copy()
        if diferencia.total_seconds() > SENSOR_TIMEOUT_SECONDS:
            response_data["status"] = "offline"
        else:
            response_data["status"] = "online"
        
        return jsonify(response_data)

    except Exception as e:
        # Caso 3: Ocurrió un error inesperado.
        print(f"Error en el endpoint /data: {e}")
        return jsonify({
            "status": "offline",
            "temperatura": 0.0,
            "humedad": 0.0,
            "temperatura_interna_esp": 0.0,
            "fecha": "Error en el servidor"
        }), 500

# --- Ruta /status (sin cambios) ---
@app.route("/status")
@login_required
def status():
    uptime_seconds = (datetime.now() - app.start_time).total_seconds()
    minutes, seconds = divmod(int(uptime_seconds), 60)
    hours, minutes = divmod(minutes, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"
    total_records = Registro.query.count()
    ultimos_registros = Registro.query.order_by(Registro.fecha.desc()).limit(24).all()
    if ultimos_registros:
        avg_temp = sum(r.temperatura for r in ultimos_registros) / len(ultimos_registros)
        avg_hum = sum(r.humedad for r in ultimos_registros) / len(ultimos_registros)
    else:
        avg_temp = 0.0
        avg_hum = 0.0
    return jsonify({
        "server_status": "online",
        "last_data": ultimo_dato,
        "total_records": total_records,
        "uptime": uptime_str,
        "average_temperature_last_24h": round(avg_temp, 2),
        "average_humidity_last_24h": round(avg_hum, 2)
    })

# --- Rutas de API para Flutter (sin cambios) ---
@app.route('/api/flutter/register', methods=['POST'])
def flutter_register():
    data = request.get_json()
    if not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({"success": False, "message": "Datos incompletos"}), 400
    if User.query.filter((User.username == data['username']) | (User.email == data['email'])).first():
        return jsonify({"success": False, "message": "Usuario o email ya existen."}), 409
    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({"success": True, "message": "Usuario registrado exitosamente."}), 201

@app.route('/api/flutter/login', methods=['POST'])
def flutter_login():
    data = request.get_json()
    if not all(k in data for k in ('username', 'password')):
        return jsonify({"success": False, "message": "Datos incompletos"}), 400
    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        login_user(user)
        return jsonify({"success": True, "message": "Inicio de sesión exitoso."}), 200
    return jsonify({"success": False, "message": "Credenciales inválidas."}), 401

@app.route('/api/flutter/logout', methods=['POST'])
@login_required
def flutter_logout():
    logout_user()
    return jsonify({"success": True, "message": "Cierre de sesión exitoso."}), 200

@app.route('/api/flutter/historical', methods=['GET'])
@login_required
def historical_data():
    # ----> AÑADE ESTA LÍNEA PARA DEPURAR <----
    print(">>> Petición recibida en /api/flutter/historical <<<") 
    try:
        # Obtener los últimos 100 registros (puedes ajustar este número)
        registros = Registro.query.order_by(Registro.fecha.desc()).limit(100).all()

        # Preparar los datos en formato para gráficos
        timestamps = [r.fecha.strftime("%H:%M") for r in registros][::-1]
        temperaturas = [r.temperatura for r in registros][::-1]
        humedades = [r.humedad for r in registros][::-1]

        # ----> AÑADE ESTA LÍNEA PARA DEPURAR <----
        print(f">>> Devolviendo {len(registros)} registros. <<<")

        return jsonify({
            "success": True,
            "timestamps": timestamps,
            "temperatura": temperaturas,
            "humedad": humedades
        })
    except Exception as e:
        # ----> AÑADE ESTA LÍNEA PARA DEPURAR <----
        print(f"!!! ERROR en /api/flutter/historical: {e} !!!")
        return jsonify({"success": False, "message": str(e)}), 500
    
if __name__ == "__main__":
    app.start_time = datetime.now()
    app.run(debug=True, host='0.0.0.0')
