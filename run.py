from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from models import db, Registro, User
from datetime import datetime
import os 
import pytz
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from forms import RegistrationForm, LoginForm # ¡NUEVO! Importa los formularios

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///climypy.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Genera una clave secreta fuerte si no existe
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
db.init_app(app)

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Define la vista de login

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    # Crear un usuario administrador por defecto si no existe
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', email='admin@climypy.com', is_admin=True) # <-- Cambios aquí
        admin_user.set_password('lobito200') # Tu contraseña actual
        db.session.add(admin_user)
        db.session.commit()
        print("Usuario 'admin' creado con contraseña 'lobito200' y email 'admin@climypy.com'.")

# Zona horaria Argentina
zona_arg = pytz.timezone("America/Argentina/Buenos_Aires")

# Variables globales para almacenar últimos datos
# Esto es para mantener el último dato en memoria, independientemente del login
ultimo_dato = {
    "temperatura": 0.0,
    "humedad": 0.0,
    "fecha": datetime.now(zona_arg).strftime("%Y-%m-%d %H:%M:%S")
}

@app.route("/")
@login_required # Esta página requiere que el usuario esté logeado
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

# --- Modifica tu ruta de Login para usar LoginForm de forms.py ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('Ya has iniciado sesión.', 'info')
        return redirect(url_for('index'))
    form = LoginForm() # Usar LoginForm de forms.py
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
@login_required # Solo usuarios logeados pueden desloguearse
def logout():
    logout_user()
    flash("Has cerrado sesión.", "info")
    return redirect(url_for('login'))


@app.route("/api/sensor", methods=["POST"])
def recibir_datos():
    try:
        datos = request.get_json()

        if not datos or 'temperatura' not in datos or 'humedad' not in datos:
            return jsonify({"error": "Datos incompletos"}), 400

        # Actualizar datos globales
        fecha_actual = datetime.now(zona_arg).strftime("%Y-%m-%d %H:%M:%S")
        ultimo_dato["temperatura"] = float(datos["temperatura"])
        ultimo_dato["humedad"] = float(datos["humedad"])
        ultimo_dato["fecha"] = fecha_actual

        # Guardar en la base de datos
        nuevo_registro = Registro(
            temperatura=float(datos["temperatura"]),
            humedad=float(datos["humedad"]),
            fecha=datetime.now(zona_arg) # Guarda el objeto datetime
        )
        db.session.add(nuevo_registro)
        db.session.commit()

        print(f"[{fecha_actual}] Datos recibidos y guardados: Temp: {datos['temperatura']}°C, Hum: {datos['humedad']}%")

        return jsonify({"status": "success", "message": "Datos guardados correctamente"}), 200

    except Exception as e:
        print(f"Error procesando datos: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/data")
@login_required # Esta API también requerirá login si los datos son privados
def data():
    """Endpoint para obtener los últimos datos (compatibilidad con frontend)"""
    return jsonify(ultimo_dato)

@app.route("/grafico")
@login_required # Protege esta ruta
def grafico():
    return render_template("grafico.html")

@app.route("/api/registros")
@login_required # Protege esta API
def api_registros():
    registros = Registro.query.order_by(Registro.fecha.desc()).limit(100).all()
    registros.reverse()  # Para mostrar en orden cronológico

    data = {
        "fechas": [r.fecha.strftime("%H:%M:%S") for r in registros], # Formatear fecha para el gráfico
        "temperaturas": [r.temperatura for r in registros],
        "humedades": [r.humedad for r in registros]
    }
    return jsonify(data)

@app.route("/registros")
@login_required # Protege esta ruta
def registros():
    registros = Registro.query.order_by(Registro.fecha.desc()).all()
    return render_template("registros.html", registros=registros)

@app.route("/status")
@login_required # Protege esta ruta
def status():
    # Calcular uptime
    uptime_seconds = (datetime.now() - app.start_time).total_seconds()
    minutes, seconds = divmod(int(uptime_seconds), 60)
    hours, minutes = divmod(minutes, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"

    total_records = Registro.query.count()

    # Calcular promedios de los últimos 24 registros (ajustable)
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


if __name__ == "__main__":
    app.start_time = datetime.now() # Registrar el tiempo de inicio de la app
    app.run(debug=True, host='0.0.0.0')