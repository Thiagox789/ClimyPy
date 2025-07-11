from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User # Importamos el modelo User para validaciones

class RegistrationForm(FlaskForm):
    username = StringField('Nombre de Usuario',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Contraseña',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ese nombre de usuario ya está en uso. Por favor, elige uno diferente.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Ese email ya está registrado. Por favor, utiliza uno diferente.')

class LoginForm(FlaskForm): # También creamos el LoginForm aquí para consistencia
    username = StringField('Nombre de Usuario',
                           validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember = BooleanField('Recuérdame')
    submit = SubmitField('Iniciar Sesión')

class SensorConfigForm(FlaskForm):
    name_temp_1 = StringField('Nombre Temperatura Sensor 1', default='Sensor 1 - Temperatura')
    name_hum_1 = StringField('Nombre Humedad Sensor 1', default='Sensor 1 - Humedad')
    name_temp_2 = StringField('Nombre Temperatura Sensor 2', default='Sensor 2 - Temperatura')
    name_hum_2 = StringField('Nombre Humedad Sensor 2', default='Sensor 2 - Humedad')
    name_temp_3 = StringField('Nombre Temperatura Sensor 3', default='Sensor 3 - Temperatura')
    name_hum_3 = StringField('Nombre Humedad Sensor 3', default='Sensor 3 - Humedad')
    name_temp_4 = StringField('Nombre Temperatura Sensor 4', default='Sensor 4 - Temperatura')
    name_hum_4 = StringField('Nombre Humedad Sensor 4', default='Sensor 4 - Humedad')
    name_temp_5 = StringField('Nombre Temperatura Sensor 5', default='Sensor 5 - Temperatura')
    name_hum_5 = StringField('Nombre Humedad Sensor 5', default='Sensor 5 - Humedad')
    submit = SubmitField('Guardar Nombres de Sensores')
