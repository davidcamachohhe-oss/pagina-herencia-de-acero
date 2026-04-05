#!/usr/bin/env python
"""
Script para inicializar la base de datos con todas las tablas necesarias
Uso: python migrate_db.py
"""

import sqlite3
import os
import sys
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_FILE = os.path.join(DATA_DIR, 'reservas.db')

def init_database():
    """Inicializar base de datos con todas las tablas"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        logger.info(f"📁 Carpeta data creada en: {DATA_DIR}")
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Tabla de reservas (actualizada)
        logger.info("📝 Creando tabla: reservas")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reservas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                email TEXT NOT NULL,
                telefono TEXT NOT NULL,
                fecha_evento TEXT NOT NULL,
                hora_evento TEXT NOT NULL,
                mensaje TEXT,
                estado TEXT DEFAULT 'pendiente',
                creado DATETIME DEFAULT CURRENT_TIMESTAMP,
                actualizado DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de auditoría
        logger.info("📝 Creando tabla: audit_log")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                accion TEXT NOT NULL,
                usuario TEXT,
                reserva_id INTEGER,
                detalles TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                FOREIGN KEY (reserva_id) REFERENCES reservas(id)
            )
        """)
        
        # Tabla de pagos (para integración futura)
        logger.info("📝 Creando tabla: pagos")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reserva_id INTEGER NOT NULL,
                monto DECIMAL(10, 2),
                estado TEXT DEFAULT 'pendiente',
                referencia_pago TEXT,
                fecha_pago DATETIME,
                metodo TEXT,
                creado DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reserva_id) REFERENCES reservas(id)
            )
        """)
        
        # Tabla de testimonios
        logger.info("📝 Creando tabla: testimonios")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS testimonios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                email TEXT NOT NULL,
                tipo_evento TEXT,
                calificacion INTEGER CHECK(calificacion >= 1 AND calificacion <= 5),
                comentario TEXT NOT NULL,
                estado TEXT DEFAULT 'pendiente',
                creado DATETIME DEFAULT CURRENT_TIMESTAMP,
                aprobado DATETIME
            )
        """)
        
        # Crear índices para mejor performance
        logger.info("📊 Creando índices")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reservas_estado ON reservas(estado)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reservas_fecha ON reservas(fecha_evento)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_accion ON audit_log(accion)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)")
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Base de datos inicializada correctamente en: {DB_FILE}")
        logger.info("📊 Tablas creadas: reservas, audit_log, pagos, testimonios")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error iniciando base de datos: {e}")
        return False

def check_database():
    """Verificar que la base de datos está bien"""
    try:
        if not os.path.exists(DB_FILE):
            logger.warning("⚠️ Base de datos no existe. Ejecutando init_database()...")
            return init_database()
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Verificar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        logger.info("📊 Tablas en la base de datos:")
        for table in tables:
            logger.info(f"  ✓ {table[0]}")
        
        # Verificar registros
        cursor.execute("SELECT COUNT(*) FROM reservas")
        reservas_count = cursor.fetchone()[0]
        logger.info(f"📋 Total de reservas: {reservas_count}")
        
        cursor.execute("SELECT COUNT(*) FROM audit_log")
        audit_count = cursor.fetchone()[0]
        logger.info(f"📋 Registros en audit log: {audit_count}")
        
        conn.close()
        logger.info("✅ Base de datos está en buen estado")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando base de datos: {e}")
        return False

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🗄️  INICIALIZADOR DE BASE DE DATOS - Herencia de Acero")
    logger.info("=" * 60)
    
    if init_database():
        logger.info("")
        check_database()
    
    logger.info("=" * 60)
