# run.py - VERSIÓN FINAL Y COMPLETA

from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
from models import db, Registro, User, SensorConfig # Importar SensorConfig
from datetime import datetime, timedelta
import os
import pytz
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from forms import RegistrationForm, LoginForm, SensorConfigForm # Importar SensorConfigForm

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

# Creación de tablas, usuario admin y configuración de sensores por defecto
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', email='admin@climypy.com', is_admin=True)
        admin_user.set_password('lobito200')
        db.session.add(admin_user)
        db.session.commit()
        print("Usuario 'admin' creado con contraseña 'lobito200' y email 'admin@climypy.com'.")
    
    # Crear configuraciones de sensores por defecto si no existen
    for i in range(1, 6):
        if not SensorConfig.query.filter_by(sensor_number=i).first():
            default_temp_name = f"Sensor {i} - Temperatura"
            default_hum_name = f"Sensor {i} - Humedad"
            sensor_config = SensorConfig(sensor_number=i, name_temp=default_temp_name, name_hum=default_hum_name)
            db.session.add(sensor_config)
    db.session.commit()
    print("Configuraciones de sensores por defecto creadas/verificadas.")

# Zona horaria
zona_arg = pytz.timezone("America/Argentina/Buenos_Aires")

# --- CAMBIO 1: Variable global inicializada en None ---
# Esto nos permite saber si alguna vez hemos recibido datos del sensor.
ultimo_dato = {
    "temperatura": None,
    "humedad": None,
    "temperatura2": None,
    "humedad2": None,
    "temperatura3": None,
    "humedad3": None,
    "temperatura4": None,
    "humedad4": None,
    "temperatura5": None,
    "humedad5": None,
    "fecha": None,
    "temperatura_interna_esp": None # Temperatura interna del chip
}

# --- Rutas para la interfaz web ---
@app.route("/")
@login_required
def index():
    # Obtener los nombres de los sensores de la base de datos
    sensor_configs = SensorConfig.query.order_by(SensorConfig.sensor_number).all()
    sensor_names = {
        config.sensor_number: {
            'temp': config.name_temp,
            'hum': config.name_hum
        } for config in sensor_configs
    }
    return render_template("index.html", sensor_names=sensor_names)

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

# Ruta para el panel de administración de sensores
@app.route("/admin/sensors", methods=['GET', 'POST'])
@login_required
def admin_sensors():
    if not current_user.is_admin:
        flash('No tienes permisos para acceder a esta página.', 'danger')
        return redirect(url_for('index'))

    form = SensorConfigForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        for i in range(1, 6):
            sensor_config = SensorConfig.query.filter_by(sensor_number=i).first()
            if sensor_config:
                sensor_config.name_temp = getattr(form, f'name_temp_{i}').data
                sensor_config.name_hum = getattr(form, f'name_hum_{i}').data
            else:
                # Esto no debería pasar si se crean por defecto al inicio
                new_config = SensorConfig(
                    sensor_number=i,
                    name_temp=getattr(form, f'name_temp_{i}').data,
                    name_hum=getattr(form, f'name_hum_{i}').data
                )
                db.session.add(new_config)
        db.session.commit()
        flash('Nombres de sensores actualizados exitosamente!', 'success')
        return redirect(url_for('admin_sensors'))
    
    # GET request: Cargar los datos actuales en el formulario
    sensor_configs = SensorConfig.query.order_by(SensorConfig.sensor_number).all()
    for config in sensor_configs:
        setattr(form, f'name_temp_{config.sensor_number}', config.name_temp)
        setattr(form, f'name_hum_{config.sensor_number}', config.name_hum)
    
    return render_template('admin_sensors.html', title='Administrar Sensores', form=form)

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
        if not datos:
            return jsonify({"error": "No se recibieron datos"}), 400

        fecha_actual = datetime.now(zona_arg).strftime("%Y-%m-%d %H:%M:%S")
        
        # Crear un diccionario para los datos del nuevo registro
        registro_data = {"fecha": datetime.now(zona_arg)}

        # Iterar sobre los posibles sensores (1 a 5)
        for i in range(1, 6):
            temp_key = f"temperatura{i}" if i > 1 else "temperatura"
            hum_key = f"humedad{i}" if i > 1 else "humedad"

            if temp_key in datos and datos[temp_key] is not None:
                ultimo_dato[temp_key] = float(datos[temp_key])
                registro_data[temp_key] = float(datos[temp_key])
            else:
                ultimo_dato[temp_key] = None # Asegurarse de que esté en None si no se envía

            if hum_key in datos and datos[hum_key] is not None:
                ultimo_dato[hum_key] = float(datos[hum_key])
                registro_data[hum_key] = float(datos[hum_key])
            else:
                ultimo_dato[hum_key] = None # Asegurarse de que esté en None si no se envía

        # Guardar la temperatura del chip ESP32 solo en memoria, si es que viene
        ultimo_dato["temperatura_interna_esp"] = datos.get("temperatura_interna_esp")
        ultimo_dato["fecha"] = fecha_actual

        # Crear el nuevo registro con los datos recibidos
        nuevo_registro = Registro(**registro_data)
        db.session.add(nuevo_registro)
        db.session.commit()

        log_message = f"[{fecha_actual}] Datos recibidos:"
        for i in range(1, 6):
            temp_key = f"temperatura{i}" if i > 1 else "temperatura"
            hum_key = f"humedad{i}" if i > 1 else "humedad"
            if ultimo_dato.get(temp_key) is not None:
                log_message += f" T{i}: {ultimo_dato[temp_key]}°C,"
            if ultimo_dato.get(hum_key) is not None:
                log_message += f" H{i}: {ultimo_dato[hum_key]}%,"
        
        if ultimo_dato.get('temperatura_interna_esp') is not None:
            log_message += f" Temp. ESP: {ultimo_dato['temperatura_interna_esp']}°C"
        
        print(log_message.strip(',')) # Eliminar la última coma si existe
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
    # Caso 1: El servidor acaba de iniciar y nunca ha recibido datos.
    if ultimo_dato.get("fecha") is None:
        # Devolvemos un diccionario con todos los campos inicializados a 0.0 o None
        # para que el frontend pueda procesarlos sin errores.
        initial_data = {
            "status": "offline",
            "fecha": "Aguardando datos del sensor..."
        }
        for key in ultimo_dato:
            if key not in ["fecha", "temperatura_interna_esp"]: # No sobrescribir estos
                initial_data[key] = 0.0 if "temperatura" in key or "humedad" in key else None
            elif key == "temperatura_interna_esp":
                initial_data[key] = 0.0
        return jsonify(initial_data)

    try:
        # Caso 2: Ya hemos recibido datos, comprobamos si son recientes.
        fecha_ultimo_dato = datetime.strptime(ultimo_dato["fecha"], "%Y-%m-%d %H:%M:%S")
        fecha_ultimo_dato = zona_arg.localize(fecha_ultimo_dato)
        ahora = datetime.now(zona_arg)
        diferencia = ahora - fecha_ultimo_dato

        response_data = ultimo_dato.copy()
        if diferencia.total_seconds() > SENSOR_TIMEOUT_SECONDS:
            response_data["status"] = "offline"
            # Si está offline, podemos limpiar los valores para que el frontend muestre "--"
            for key in response_data:
                if "temperatura" in key or "humedad" in key:
                    response_data[key] = None
        else:
            response_data["status"] = "online"
        
        return jsonify(response_data)

    except Exception as e:
        # Caso 3: Ocurrió un error inesperado.
        print(f"Error en el endpoint /data: {e}")
        # Devolvemos un diccionario con todos los campos inicializados a 0.0 o None
        error_data = {
            "status": "offline",
            "fecha": "Error en el servidor"
        }
        for key in ultimo_dato:
            if key not in ["fecha", "temperatura_interna_esp"]:
                error_data[key] = None
            elif key == "temperatura_interna_esp":
                error_data[key] = None
        return jsonify(error_data), 500

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
    
    response_data = {
        "server_status": "online",
        "last_data": ultimo_dato,
        "total_records": total_records,
        "uptime": uptime_str,
    }

    # Calcular promedios para cada sensor
    for i in range(1, 6):
        temp_key = f"temperatura{i}" if i > 1 else "temperatura"
        hum_key = f"humedad{i}" if i > 1 else "humedad"
        
        temps = [getattr(r, temp_key) for r in ultimos_registros if getattr(r, temp_key) is not None]
        hums = [getattr(r, hum_key) for r in ultimos_registros if getattr(r, hum_key) is not None]

        response_data[f"average_{temp_key}_last_24h"] = round(sum(temps) / len(temps), 2) if temps else 0.0
        response_data[f"average_{hum_key}_last_24h"] = round(sum(hums) / len(hums), 2) if hums else 0.0
    
    return jsonify(response_data)

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
        
        response_data = {
            "success": True,
            "timestamps": timestamps
        }

        for i in range(1, 6):
            temp_key = f"temperatura{i}" if i > 1 else "temperatura"
            hum_key = f"humedad{i}" if i > 1 else "humedad"
            
            response_data[temp_key] = [getattr(r, temp_key) for r in registros][::-1]
            response_data[hum_key] = [getattr(r, hum_key) for r in registros][::-1]

        # ----> AÑADE ESTA LÍNEA PARA DEPURAR <----
        print(f">>> Devolviendo {len(registros)} registros. <<<")

        return jsonify(response_data)
    except Exception as e:
        # ----> AÑADE ESTA LÍNEA PARA DEPURAR <----
        print(f"!!! ERROR en /api/flutter/historical: {e} !!!")
        return jsonify({"success": False, "message": str(e)}), 500
    
if __name__ == "__main__":
    app.start_time = datetime.now()
    app.run(debug=True, host='0.0.0.0')
