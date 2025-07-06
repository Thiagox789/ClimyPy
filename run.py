from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
from models import db, Registro, User
from datetime import datetime
import os
import pytz
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from forms import RegistrationForm, LoginForm

app = Flask(__name__)
# Configuración de la base de datos SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///climypy.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False # Desactiva el seguimiento de modificaciones de objetos
# Genera una clave secreta fuerte si no existe, crucial para la seguridad de la sesión
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
db.init_app(app) # Inicializa la base de datos con la aplicación Flask

# Configuración de Flask-Login para manejar sesiones de usuario
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Define la vista a la que se redirige si se requiere login

# Función para cargar un usuario desde la base de datos por su ID
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Crea las tablas de la base de datos y un usuario administrador por defecto
with app.app_context():
    db.create_all() # Crea todas las tablas definidas en models.py
    # Crear un usuario administrador por defecto si no existe
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', email='admin@climypy.com', is_admin=True)
        admin_user.set_password('lobito200') # Contraseña inicial para el admin
        db.session.add(admin_user)
        db.session.commit()
        print("Usuario 'admin' creado con contraseña 'lobito200' y email 'admin@climypy.com'.")

# Zona horaria Argentina para manejar fechas y horas correctamente
zona_arg = pytz.timezone("America/Argentina/Buenos_Aires")

# Variable global para almacenar el último dato recibido (para acceso rápido)
ultimo_dato = {
    "temperatura": 0.0,
    "humedad": 0.0,
    "fecha": datetime.now(zona_arg).strftime("%Y-%m-%d %H:%M:%S")
}

# --- Rutas para la interfaz web (HTML) ---
# Estas rutas sirven páginas HTML y requieren que el usuario esté logeado
@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('Ya has iniciado sesión.', 'info')
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
        flash('Ya has iniciado sesión.', 'info')
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash('¡Inicio de sesión exitoso!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Inicio de sesión fallido. Por favor, verifica tu usuario y contraseña.', 'danger')
    return render_template('login.html', title='Iniciar Sesión', form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión.", "info")
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

# --- Rutas de API para el sensor (recibe datos del hardware, no requiere login) ---
@app.route("/api/sensor", methods=["POST"])
def recibir_datos():
    try:
        datos = request.get_json()
        if not datos or 'temperatura' not in datos or 'humedad' not in datos:
            return jsonify({"error": "Datos incompletos"}), 400

        fecha_actual = datetime.now(zona_arg).strftime("%Y-%m-%d %H:%M:%S")
        ultimo_dato["temperatura"] = float(datos["temperatura"])
        ultimo_dato["humedad"] = float(datos["humedad"])
        ultimo_dato["fecha"] = fecha_actual

        nuevo_registro = Registro(
            temperatura=float(datos["temperatura"]),
            humedad=float(datos["humedad"]),
            fecha=datetime.now(zona_arg)
        )
        db.session.add(nuevo_registro)
        db.session.commit()

        print(f"[{fecha_actual}] Datos recibidos y guardados: Temp: {datos['temperatura']}°C, Hum: {datos['humedad']}%")
        return jsonify({"status": "success", "message": "Datos guardados correctamente"}), 200

    except Exception as e:
        print(f"Error procesando datos: {e}")
        return jsonify({"error": str(e)}), 500

# --- Rutas de API para la aplicación Flutter (requieren login para acceder a datos) ---

@app.route("/data")
@login_required # Esta API ahora requiere que el usuario esté logeado (desde Flutter o web)
def data():
    """Endpoint para obtener los últimos datos (compatibilidad con frontend y bot)"""
    return jsonify(ultimo_dato)

@app.route("/status")
@login_required # Esta API ahora requiere que el usuario esté logeado (desde Flutter o web)
def status():
    """Endpoint para obtener estadísticas (compatibilidad con frontend y bot)"""
    # Calcula el tiempo de actividad del servidor
    uptime_seconds = (datetime.now() - app.start_time).total_seconds()
    minutes, seconds = divmod(int(uptime_seconds), 60)
    hours, minutes = divmod(minutes, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"

    # Obtiene el total de registros en la base de datos
    total_records = Registro.query.count()

    # Calcula promedios de los últimos 24 registros (ajustable)
    ultimos_registros = Registro.query.order_by(Registro.fecha.desc()).limit(24).all()
    if ultimos_registros:
        avg_temp = sum(r.temperatura for r in ultimos_registros) / len(ultimos_registros)
        avg_hum = sum(r.humedad for r in ultimos_registros) / len(ultimos_registros)
    else:
        avg_temp = 0.0
        avg_hum = 0.0

    # Devuelve los datos en formato JSON
    return jsonify({
        "server_status": "online",
        "last_data": ultimo_dato,
        "total_records": total_records,
        "uptime": uptime_str,
        "average_temperature_last_24h": round(avg_temp, 2),
        "average_humidity_last_24h": round(avg_hum, 2)
    })

# NUEVA RUTA API para el registro desde la app Flutter
@app.route('/api/flutter/register', methods=['POST'])
def flutter_register():
    data = request.get_json() # Obtiene los datos JSON de la petición
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # Valida que los datos necesarios estén presentes
    if not username or not email or not password:
        return jsonify({"success": False, "message": "Datos incompletos"}), 400

    # Verifica si el nombre de usuario o email ya existen
    if User.query.filter_by(username=username).first():
        return jsonify({"success": False, "message": "Ese nombre de usuario ya está en uso."}), 409 # Conflict
    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "message": "Ese email ya está registrado."}), 409 # Conflict

    try:
        # Crea un nuevo usuario y lo guarda en la base de datos
        user = User(username=username, email=email)
        user.set_password(password) # Hashea la contraseña
        db.session.add(user)
        db.session.commit()
        return jsonify({"success": True, "message": "Usuario registrado exitosamente."}), 201 # Created
    except Exception as e:
        db.session.rollback() # Revierte la transacción si hay un error
        return jsonify({"success": False, "message": f"Error al registrar usuario: {str(e)}"}), 500 # Internal Server Error

# NUEVA RUTA API para el login desde la app Flutter
@app.route('/api/flutter/login', methods=['POST'])
def flutter_login():
    data = request.get_json() # Obtiene los datos JSON de la petición
    username = data.get('username')
    password = data.get('password')

    # Valida que los datos necesarios estén presentes
    if not username or not password:
        return jsonify({"success": False, "message": "Usuario o contraseña incompletos"}), 400 # Bad Request

    user = User.query.filter_by(username=username).first() # Busca el usuario
    # Verifica la contraseña
    if user and user.check_password(password):
        login_user(user) # Inicia sesión con Flask-Login (maneja la cookie de sesión)
        return jsonify({"success": True, "message": "Inicio de sesión exitoso."}), 200 # OK
    else:
        return jsonify({"success": False, "message": "Credenciales inválidas."}), 401 # Unauthorized

# NUEVA RUTA API para el logout desde la app Flutter
@app.route('/api/flutter/logout', methods=['POST'])
@login_required # Solo usuarios logeados pueden desloguearse
def flutter_logout():
    logout_user() # Cierra la sesión con Flask-Login
    return jsonify({"success": True, "message": "Cierre de sesión exitoso."}), 200 # OK


if __name__ == "__main__":
    app.start_time = datetime.now() # Registra el tiempo de inicio de la aplicación
    app.run(debug=True, host='0.0.0.0') # Inicia el servidor Flask en modo debug, accesible desde cualquier IP
