from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin # Importar UserMixin

db = SQLAlchemy()

# Clase para los registros de temperatura y humedad
class Registro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperatura = db.Column(db.Float, nullable=True) # Hacemos nullable para permitir datos parciales
    humedad = db.Column(db.Float, nullable=True)     # Hacemos nullable para permitir datos parciales
    temperatura2 = db.Column(db.Float, nullable=True)
    humedad2 = db.Column(db.Float, nullable=True)
    temperatura3 = db.Column(db.Float, nullable=True)
    humedad3 = db.Column(db.Float, nullable=True)
    temperatura4 = db.Column(db.Float, nullable=True)
    humedad4 = db.Column(db.Float, nullable=True)
    temperatura5 = db.Column(db.Float, nullable=True)
    humedad5 = db.Column(db.Float, nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow) # Guarda la fecha en UTC por defecto

    def __repr__(self):
        return f"<Registro {self.id} - T1:{self.temperatura}°C, H1:{self.humedad}%>"

# Clase para la configuración de los nombres de los sensores
class SensorConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensor_number = db.Column(db.Integer, unique=True, nullable=False) # 1, 2, 3, 4, 5
    name_temp = db.Column(db.String(50), default="Temperatura")
    name_hum = db.Column(db.String(50), default="Humedad")

    def __repr__(self):
        return f"<SensorConfig {self.sensor_number} - Temp: {self.name_temp}, Hum: {self.name_hum}>"

# Clase para los usuarios del sistema (login)
class User(UserMixin, db.Model): # Hereda de UserMixin
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False) # Nuevo: Campo para el email
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False) # Nuevo: Campo para el rol de administrador

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"
