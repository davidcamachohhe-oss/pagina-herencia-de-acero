"""
Módulo de base de datos PostgreSQL para Herencia de Acero
"""
import os
import logging
import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL', '').replace('postgres://', 'postgresql://')


def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def row_to_dict(cursor, row):
    if row is None:
        return None
    cols = [desc[0] for desc in cursor.description]
    return dict(zip(cols, row))


def rows_to_dicts(cursor, rows):
    cols = [desc[0] for desc in cursor.description]
    return [dict(zip(cols, row)) for row in rows]


def init_db():
    """Crear tablas si no existen"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS reservas(
        id SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL,
        email TEXT NOT NULL,
        telefono TEXT NOT NULL,
        fecha_evento TEXT NOT NULL,
        hora_evento TEXT NOT NULL,
        mensaje TEXT,
        estado TEXT DEFAULT 'pendiente',
        creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        actualizado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS audit_log (
        id SERIAL PRIMARY KEY,
        accion TEXT NOT NULL,
        usuario TEXT,
        reserva_id INTEGER,
        detalles TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS testimonios (
        id SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL,
        email TEXT NOT NULL,
        tipo_evento TEXT,
        calificacion INTEGER DEFAULT 5,
        comentario TEXT NOT NULL,
        estado TEXT DEFAULT 'pendiente',
        creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        aprobado TIMESTAMP
    )""")
    conn.commit()
    cur.close()
    conn.close()
    logger.info("Base de datos PostgreSQL inicializada")
