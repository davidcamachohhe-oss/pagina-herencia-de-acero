#!/usr/bin/env python
"""
Script de setup completo para el proyecto
Ejecuta: python setup.py
"""

import os
import sys
import subprocess
import bcrypt
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_env_file():
    """Verificar que existe .env"""
    print_header("✓ VERIFICANDO CONFIGURACIÓN")
    
    if not os.path.exists('.env'):
        logger.warning("❌ Archivo .env no encontrado")
        logger.info("📝 Copiar .env.example a .env y llenar credenciales")
        return False
    
    logger.info("✓ Archivo .env encontrado")
    return True

def install_dependencies():
    """Instalar dependencias"""
    print_header("📦 INSTALANDO DEPENDENCIAS")
    
    if not os.path.exists('requirements.txt'):
        logger.error("❌ requirements.txt no encontrado")
        return False
    
    try:
        logger.info("Installing packages...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt', '-q'])
        logger.info("✓ Dependencias instaladas")
        return True
    except Exception as e:
        logger.error(f"❌ Error instalando dependencias: {e}")
        return False

def create_directories():
    """Crear directorios necesarios"""
    print_header("📁 CREANDO DIRECTORIOS")
    
    dirs = ['data', 'static', 'logs']
    for dir_name in dirs:
        try:
            os.makedirs(dir_name, exist_ok=True)
            logger.info(f"✓ Carpeta creada: {dir_name}/")
        except Exception as e:
            logger.error(f"❌ Error creando {dir_name}/: {e}")
            return False
    
    return True

def init_database():
    """Inicializar base de datos"""
    print_header("🗄️  INICIALIZANDO BASE DE DATOS")
    
    try:
        from migrate_db import init_database
        result = init_database()
        if result:
            logger.info("✓ Base de datos inicializada")
            return True
        else:
            logger.error("❌ Error al inicializar base de datos")
            return False
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

def generate_password_hash():
    """Generar hash para contraseña de admin"""
    print_header("🔐 GENERANDO HASH DE CONTRASEÑA")
    
    password = input("Ingresa la contraseña de admin (default: herencia2026): ").strip()
    if not password:
        password = 'herencia2026'
    
    try:
        hash_obj = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        hash_str = hash_obj.decode()
        
        logger.info("✓ Hash generado (guarda esto en .env como ADMIN_PASSWORD_HASH):")
        print(f"\n  {hash_str}\n")
        
        return hash_str
    except Exception as e:
        logger.error(f"❌ Error generando hash: {e}")
        return None

def setup_complete():
    """Mostrar resumen final"""
    print_header("✅ SETUP COMPLETADO")
    
    logger.info("""
🎵 Proyecto Herencia de Acero - Listo para ejecutar

Próximos pasos:
1. Editar .env con tus credenciales reales
2. Guardar el hash de contraseña en ADMIN_PASSWORD_HASH
3. Agregar archivos de imagen y video a /static/
4. Ejecutar: python app.py
5. Abrir: http://localhost:5000

Documentación de seguridad:
- REPORTE_ERRORES.md: Análisis de vulnerabilidades
- SOLUCIONES_SEGURIDAD.md: Cómo corregir
- ARCHIVOS_ESTATICOS_FALTANTES.md: Qué archivos necesitas

¡Gracias por usar Herencia de Acero!
    """)

if __name__ == '__main__':
    print_header("🎵 SETUP - HERENCIA DE ACERO 2026")
    
    steps = [
        ("Verificar configuración", check_env_file),
        ("Crear directorios", create_directories),
        ("Instalar dependencias", install_dependencies),
        ("Inicializar base de datos", init_database),
    ]
    
    for step_name, step_func in steps:
        logger.info(f"\n📍 {step_name}...")
        if not step_func():
            logger.error(f"❌ Falló: {step_name}")
            logger.info("Por favor, completa este paso manualmente")
        else:
            logger.info(f"✓ {step_name} completado")
    
    # Generar hash
    generate_password_hash()
    
    # Mostrar resumen
    setup_complete()
