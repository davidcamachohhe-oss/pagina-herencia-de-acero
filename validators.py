"""
Validadores para el sistema de reservas
"""
import re
from datetime import datetime
from email_validator import validate_email, EmailNotValidError


def validar_email(email):
    """Validar formato de email"""
    try:
        valid = validate_email(email)
        return True, valid.email
    except EmailNotValidError as e:
        return False, str(e)


def validar_telefono(telefono):
    """Validar teléfono colombiano"""
    # Formato: +57 312 345 6789 o variantes
    patron = r'^(\+57|0)?[\s]?[0-9]{10}$'
    clean_phone = telefono.replace(' ', '').replace('-', '')
    if re.match(patron, clean_phone):
        return True, telefono
    return False, "Teléfono inválido. Formato: +57 316 123 4567"


def validar_fecha_evento(fecha_str):
    """Validar que sea fecha válida y futura"""
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
        ahora = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if fecha < ahora:
            return False, "La fecha no puede ser anterior a hoy"
        return True, fecha
    except ValueError:
        return False, "Formato de fecha inválido (YYYY-MM-DD)"


def validar_hora(hora_str):
    """Validar formato de hora"""
    try:
        datetime.strptime(hora_str, '%H:%M')
        return True, hora_str
    except ValueError:
        return False, "Formato de hora inválido (HH:MM)"


def validar_tipo_evento(tipo):
    """Validar que tipo de evento sea permitido"""
    TIPOS_PERMITIDOS = ['privado_ibague', 'privado_fuera', 'masivo_ibague', 'masivo_fuera']
    if tipo in TIPOS_PERMITIDOS:
        return True, tipo
    return False, f"Tipo de evento inválido"


def validar_cantidad_musicos(cantidad_str):
    """Validar que cantidad de músicos sea válida"""
    try:
        cantidad = int(cantidad_str)
        if cantidad in [7, 9, 11]:
            return True, cantidad
        return False, "Cantidad debe ser 7, 9 u 11 músicos"
    except (ValueError, TypeError):
        return False, "Cantidad de músicos inválida"


def validar_horas(horas_str):
    """Validar cantidad de horas"""
    try:
        horas = int(horas_str)
        if 1 <= horas <= 12:
            return True, horas
        return False, "Las horas deben estar entre 1 y 12"
    except (ValueError, TypeError):
        return False, "Cantidad de horas inválida"


def validar_nombre(nombre):
    """Validar nombre (mínimo 3 caracteres, máximo 100)"""
    nombre = nombre.strip()
    if len(nombre) < 3:
        return False, "El nombre debe tener al menos 3 caracteres"
    if len(nombre) > 100:
        return False, "El nombre es demasiado largo"
    return True, nombre


def validar_mensaje(mensaje):
    """Validar mensaje adicional"""
    if mensaje and len(mensaje) > 500:
        return False, "El mensaje es demasiado largo (máximo 500 caracteres)"
    return True, mensaje
