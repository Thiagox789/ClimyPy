from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin # Importar UserMixin

db = SQLAlchemy()

# Clase para los registros de temperatura y humedad
class Registro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperatura = db.Column(db.Float, nullable=False)
    humedad = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow) # Guarda la fecha en UTC por defecto

    def __repr__(self):
        return f"<Registro {self.temperatura}°C, {self.humedad}%, {self.fecha}>"

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