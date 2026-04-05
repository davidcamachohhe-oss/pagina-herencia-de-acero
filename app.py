# Código principal de Flask con dashboard, reservas y correo
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_mail import Mail, Message
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sqlite3, os, logging, threading
from datetime import datetime, timedelta
from dotenv import load_dotenv
from config import get_config
from validators import *
import bcrypt

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Cargar configuración
env = os.getenv('FLASK_ENV', 'development')
app.config.from_object(get_config(env))

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Asegurar carpetas necesarias
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
DATA_DIR = os.path.join(BASE_DIR, 'data')

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)




# Inicializar correo
mail = Mail(app)

# Base de datos (usar carpeta data protegida)
DB_FILE = os.path.join(DATA_DIR, 'reservas.db')

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def generar_link_calendar(reserva):
    """Genera un link para agregar el evento a Google Calendar"""
    from urllib.parse import quote
    
    try:
        fecha_str = reserva['fecha_evento'].replace('-', '')  # YYYYMMDD
        
        hora_raw = reserva['hora_evento'] or '00:00'
        # Soportar HH:MM y HH:MM:SS
        hora_parts = hora_raw.strip().split(':')
        hora_obj = datetime.strptime(f"{hora_parts[0]}:{hora_parts[1]}", '%H:%M')
        
        # Inicio
        inicio = f"{fecha_str}T{hora_obj.strftime('%H%M')}00"
        
        # Fin (sumar 2 horas por defecto)
        horas = 2
        try:
            horas = int(reserva['horas'])
        except (KeyError, TypeError, ValueError):
            pass
        fin_dt = hora_obj + timedelta(hours=horas)
        fin = f"{fecha_str}T{fin_dt.strftime('%H%M')}00"
        
        titulo = quote(f"Evento Musical - Herencia de Acero")
        detalle = quote(f"Cliente: {reserva['nombre']}\nTeléfono: {reserva['telefono']}\nEmail: {reserva['email']}\nDetalles: {reserva['mensaje'] or 'Sin detalles'}")
        
        link = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={titulo}&dates={inicio}/{fin}&details={detalle}&sf=true&output=xml"
        return link
    except Exception as e:
        logger.error(f"Error generando link calendar: {e}")
        return None

def registrar_audit(accion, usuario, reserva_id, detalles='', ip_address=''):
    """Registrar operación en log de auditoría"""
    try:
        conn = get_db()
        conn.execute("""
            INSERT INTO audit_log 
            (accion, usuario, reserva_id, detalles, timestamp, ip_address)
            VALUES (?, ?, ?, ?, datetime('now'), ?)
        """, (accion, usuario, reserva_id, detalles, ip_address))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error en audit log: {e}")

def enviar_confirmacion(reserva):
    try:
        calendar_link = generar_link_calendar(reserva)
        
        msg = Message(
            subject='✓ Reserva Confirmada - Herencia de Acero',
            sender=app.config['MAIL_USERNAME'],
            recipients=[reserva['email']]
        )
        msg.html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <div style="background: linear-gradient(135deg, #d4af37 0%, #e8c547 100%); padding: 20px; text-align: center;">
                    <h1 style="color: #000; margin: 0;">🎵 HERENCIA DE ACERO 🎵</h1>
                    <p style="color: #000; margin: 5px 0 0 0; font-style: italic;">Agrupación de música de banda</p>
                </div>
                
                <div style="padding: 30px; background: #f9f9f9;">
                    <h2 style="color: #d4af37;">¡Reserva Confirmada!</h2>
                    
                    <p>Hola <strong>{reserva['nombre']}</strong>,</p>
                    
                    <p>Tu reserva para <strong>Herencia de Acero</strong> ha sido <strong style="color: #d4af37;">CONFIRMADA</strong>.</p>
                    
                    <div style="background: #fff; border: 2px solid #d4af37; border-radius: 8px; padding: 20px; margin: 20px 0;">
                        <h3 style="color: #d4af37; margin-top: 0;">Detalles de tu Reserva:</h3>
                        <p><strong>📅 Fecha:</strong> {reserva['fecha_evento']}</p>
                        <p><strong>⏰ Hora:</strong> {reserva['hora_evento']}</p>
                        <p><strong>📞 Teléfono:</strong> {reserva['telefono']}</p>
                        {f'<p><strong>📝 Detalles:</strong> {reserva["mensaje"]}</p>' if reserva['mensaje'] else ''}
                    </div>

                    {f'''
                    <div style="background: #fff; border: 2px solid #4285f4; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center;">
                        <h3 style="color: #4285f4; margin-top: 0;">📅 Agregar a Google Calendar</h3>
                        <p style="margin-bottom: 15px;">Haz clic para agregar este evento a tu calendario:</p>
                        <a href="{calendar_link}" target="_blank" 
                           style="background: #4285f4; color: #fff; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; display: inline-block;">
                            📅 Agregar a Google Calendar
                        </a>
                    </div>
                    ''' if calendar_link else ''}
                    
                    <p>¡Gracias por confiar en <strong>Herencia de Acero</strong>! Nos complace mucho confirmar tu evento.</p>
                    
                    <hr style="border: 1px solid #ddd;">
                    
                    <h3 style="color: #d4af37;">Datos de Contacto:</h3>
                    <p>
                        📞 <strong>Teléfono:</strong> <a href="tel:+573165315514" style="color: #d4af37; text-decoration: none;">+57 316 5315514</a><br>
                        💬 <strong>WhatsApp:</strong> <a href="https://wa.me/573165315514" style="color: #d4af37; text-decoration: none;">+57 316 5315514</a>
                    </p>
                    
                    <h3 style="color: #d4af37;">Síguenos en Redes Sociales:</h3>
                    <div style="margin: 15px 0;">
                        <a href="https://web.facebook.com/people/Herencia-de-Acero/61580861555027/" style="color: #d4af37; text-decoration: none; margin: 0 10px;">📘 Facebook</a>
                        <a href="https://instagram.com/herenciadeacero" style="color: #d4af37; text-decoration: none; margin: 0 10px;">📷 Instagram</a>
                        <a href="https://youtube.com/@herenciadeacero" style="color: #d4af37; text-decoration: none; margin: 0 10px;">🎥 YouTube</a>
                        <a href="https://tiktok.com/@herenciadeacero" style="color: #d4af37; text-decoration: none; margin: 0 10px;">🎵 TikTok</a>
                    </div>
                </div>
                
                <div style="background: #1a1a2e; color: #999; padding: 20px; text-align: center; font-size: 12px;">
                    <p style="margin: 0;">&copy; 2026 Herencia de Acero - Banda de Música Popular</p>
                    <p style="margin: 5px 0 0 0;">Todos los derechos reservados.</p>
                </div>
            </body>
        </html>
        """
        mail.send(msg)
        return True, calendar_link
    except Exception as e:
        logger.error(f"Error enviando correo: {e}")
        return False, None

def enviar_confirmacion_async(reserva):
    """Envía el correo en un hilo separado para no bloquear el worker"""
    def _enviar():
        try:
            with app.app_context():
                enviar_confirmacion(reserva)
        except Exception as e:
            logger.error(f"Error en hilo de correo: {e}")
    t = threading.Thread(target=_enviar, daemon=True)
    t.start()

# Crear DB si no existe con tablas de auditoría
if not os.path.exists(DB_FILE):
    conn = get_db()
    # Tabla de reservas
    conn.execute("""CREATE TABLE IF NOT EXISTS reservas(
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
    )""")
    
    # Tabla de auditoría
    conn.execute("""CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        accion TEXT NOT NULL,
        usuario TEXT,
        reserva_id INTEGER,
        detalles TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT,
        FOREIGN KEY (reserva_id) REFERENCES reservas(id)
    )""")

    # Tabla de testimonios
    conn.execute("""CREATE TABLE IF NOT EXISTS testimonios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT NOT NULL,
        tipo_evento TEXT,
        calificacion INTEGER DEFAULT 5,
        comentario TEXT NOT NULL,
        estado TEXT DEFAULT 'pendiente',
        creado DATETIME DEFAULT CURRENT_TIMESTAMP,
        aprobado DATETIME
    )""")
    
    conn.commit()
    conn.close()
    logger.info("Base de datos creada con tablas de auditoría")
else:
    # Asegurar que todas las tablas existan aunque la DB ya esté creada
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS testimonios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT NOT NULL,
        tipo_evento TEXT,
        calificacion INTEGER DEFAULT 5,
        comentario TEXT NOT NULL,
        estado TEXT DEFAULT 'pendiente',
        creado DATETIME DEFAULT CURRENT_TIMESTAMP,
        aprobado DATETIME
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        accion TEXT NOT NULL,
        usuario TEXT,
        reserva_id INTEGER,
        detalles TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT,
        FOREIGN KEY (reserva_id) REFERENCES reservas(id)
    )""")
    conn.commit()
    conn.close()


@app.route('/')
def index():
    conn = get_db()
    total_eventos = conn.execute("SELECT COUNT(*) as count FROM reservas WHERE estado='confirmada'").fetchone()['count']
    conn.close()
    return render_template('index.html', total_eventos=total_eventos)

@app.route('/reservar', methods=['POST'])
@limiter.limit("10 per hour")  # Límite de intentos
def reservar():
    try:
        # VALIDAR TODOS LOS INPUTS
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        telefono = request.form.get('telefono', '').strip()
        fecha_evento = request.form.get('fecha_evento', '').strip()
        hora_evento = request.form.get('hora_evento', '').strip()
        tipo_evento = request.form.get('tipo_evento', '').strip()
        musicos = request.form.get('musicos', '').strip()
        sonido = request.form.get('sonido', '') == 'on'
        mensaje = request.form.get('mensaje', '').strip()

        # Validar nombre
        valido, nombre = validar_nombre(nombre)
        if not valido:
            flash(f'❌ Error en nombre: {nombre}', 'error')
            return redirect(url_for('index'))

        # Validar email
        valido, result = validar_email(email)
        if not valido:
            flash(f'❌ Email inválido: {result}', 'error')
            return redirect(url_for('index'))
        email = result

        # Validar teléfono
        valido, result = validar_telefono(telefono)
        if not valido:
            flash(f'❌ {result}', 'error')
            return redirect(url_for('index'))

        # Validar fecha
        valido, result = validar_fecha_evento(fecha_evento)
        if not valido:
            flash(f'❌ {result}', 'error')
            return redirect(url_for('index'))

        # Validar hora
        valido, result = validar_hora(hora_evento)
        if not valido:
            flash(f'❌ {result}', 'error')
            return redirect(url_for('index'))

        # Validar tipo evento
        valido, result = validar_tipo_evento(tipo_evento)
        if not valido:
            flash(f'❌ {result}', 'error')
            return redirect(url_for('index'))

        # Validar cantidad de músicos
        valido, result = validar_cantidad_musicos(musicos)
        if not valido:
            flash(f'❌ {result}', 'error')
            return redirect(url_for('index'))
        musicos = result

        # Validar horas
        horas = request.form.get('horas', '1')
        valido, result = validar_horas(horas)
        if not valido:
            flash(f'❌ {result}', 'error')
            return redirect(url_for('index'))
        horas = result

        # Validar mensaje
        valido, result = validar_mensaje(mensaje)
        if not valido:
            flash(f'❌ {result}', 'error')
            return redirect(url_for('index'))

        logger.info(f"[RESERVA] Procesando: {nombre} | {email} | {tipo_evento}")

        # Calcular precio con valores validados
        tarifas = {
            'privado_ibague': {7: 800000,  9: 1000000, 11: 1200000},
            'privado_fuera':  {7: 1150000, 9: 1450000, 11: 1750000},
            'masivo_ibague':  {7: 2200000, 9: 2800000, 11: 3300000},
            'masivo_fuera':   {7: 2500000, 9: 3200000, 11: 3900000},
        }
        
        precio_base = tarifas.get(tipo_evento, {}).get(musicos, 0) * horas
        precio_sonido = 200000 if sonido else 0
        precio_total = precio_base + precio_sonido
        precio_anticipo = precio_total // 2  # 50%

        # Construir detalle completo
        detalle = f"Tipo: {tipo_evento} | Musicos: {musicos} | Horas: {horas} | Total: ${precio_total:,}"
        if sonido:
            detalle += " | Con sonido adicional"
        if mensaje:
            detalle += f" | {mensaje}"

        conn = get_db()

        # Verificar si ya existe una reserva en esa fecha y hora
        existente = conn.execute("""
            SELECT id FROM reservas 
            WHERE fecha_evento=? AND hora_evento=? AND estado != 'cancelada'
        """, (fecha_evento, hora_evento)).fetchone()

        if existente:
            conn.close()
            logger.warning(f"Fecha/hora ocupada: {fecha_evento} {hora_evento}")
            return render_template('reserva_ocupada.html', fecha=fecha_evento, hora=hora_evento)

        try:
            cursor = conn.execute("""INSERT INTO reservas
                (nombre,email,telefono,fecha_evento,hora_evento,mensaje)
                VALUES (?,?,?,?,?,?)""",
                (nombre, email, telefono, fecha_evento, hora_evento, detalle))
            reserva_id = cursor.lastrowid
            conn.commit()
            
            # Registrar en auditoría
            registrar_audit('CREAR_RESERVA', 'usuario', reserva_id, detalle, request.remote_addr)
            
            logger.info(f"Reserva creada: ID={reserva_id}")
            
            # Obtener datos de la reserva para email
            reserva = conn.execute("SELECT * FROM reservas WHERE id=?", (reserva_id,)).fetchone()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error insertando reserva: {e}")
            flash('❌ Error al guardar la reserva', 'error')
            return redirect(url_for('index'))
        finally:
            conn.close()

        # Enviar correo de confirmación en background (no bloquea)
        try:
            enviar_confirmacion_async(reserva)
            registrar_audit('EMAIL_CONFIRMACION', 'usuario', reserva_id, f"Email enviado a {email}", request.remote_addr)
        except Exception as e:
            logger.warning(f"No se pudo enviar email automático: {e}")
        
        flash('¡Reserva guardada! Procede con el pago para confirmar.', 'success')
        return redirect(url_for('pagos', reserva_id=reserva_id, anticipo=precio_anticipo))
    
    except Exception as e:
        logger.error(f"Error en reservar: {e}")
        flash(f'❌ Error al procesar la reserva: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/galeria')
def galeria():
    return render_template('galeria.html')

@app.route('/testimonios')
def testimonios():
    try:
        conn = get_db()
        testimonios_list = conn.execute("""
            SELECT nombre, calificacion, comentario, tipo_evento 
            FROM testimonios 
            WHERE estado = 'aprobado' 
            ORDER BY aprobado DESC 
            LIMIT 50
        """).fetchall()
        conn.close()
        return render_template('testimonios.html', testimonios=testimonios_list)
    except Exception as e:
        logger.error(f"Error cargando testimonios: {e}")
        return render_template('testimonios.html', testimonios=[])

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/equipo')
def equipo():
    return render_template('equipo.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/cobertura')
def cobertura():
    return render_template('cobertura.html')

@app.route('/disponibilidad')
def disponibilidad():
    conn = get_db()
    reservas = conn.execute("SELECT fecha_evento, hora_evento FROM reservas WHERE estado IN ('confirmada', 'pendiente')").fetchall()
    conn.close()
    fechas_ocupadas = [{'fecha': r['fecha_evento'], 'hora': r['hora_evento']} for r in reservas]
    return render_template('disponibilidad.html', fechas_ocupadas=fechas_ocupadas)

@app.route('/gracias')
def gracias():
    conn = get_db()
    total_eventos = conn.execute("SELECT COUNT(*) as count FROM reservas WHERE estado='confirmada'").fetchone()['count']
    conn.close()
    return render_template('gracias.html', total_eventos=total_eventos)

@app.route('/pagos/<int:reserva_id>')
def pagos(reserva_id):
    conn = get_db()
    reserva = conn.execute("SELECT * FROM reservas WHERE id=?", (reserva_id,)).fetchone()
    conn.close()
    
    if not reserva:
        flash('Reserva no encontrada', 'error')
        return redirect(url_for('index'))
    
    anticipo = request.args.get('anticipo', 0, type=int)
    anticipo_centavos = anticipo * 100
    now = datetime.now().strftime('%Y%m%d%H%M%S')
    
    return render_template('pagos.html', reserva=reserva, anticipo=anticipo, anticipo_centavos=anticipo_centavos, now=now)

# PANEL ADMIN
@app.route('/admin', methods=['GET', 'POST'])
@limiter.limit("30 per hour")  # Límite total
def admin():
    # Si ya está logueado, mostrar dashboard directamente
    if request.method == 'GET' and session.get('admin_logged') == True:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        usuario = request.form.get('usuario', '').strip()
        password = request.form.get('password', '').strip()
        
        # Validar contra contraseña hasheada (CORRECTO)
        admin_user_config = app.config.get('ADMIN_USER', 'admin')
        admin_pass_hash = app.config.get('ADMIN_PASSWORD_HASH')
        
        # Si no hay hash configurado, usar valor por defecto (cambiar en producción)
        if not admin_pass_hash:
            logger.warning("⚠️ ADMIN_PASSWORD_HASH no configurado. Usando valor por defecto.")
            admin_pass_hash = bcrypt.hashpw(b'herencia2026', bcrypt.gensalt()).decode()
        
        if usuario == admin_user_config:
            try:
                # Verificar contraseña hasheada
                if bcrypt.checkpw(password.encode(), admin_pass_hash.encode()):
                    session['admin_logged'] = True
                    session['admin_user'] = usuario
                    session['login_time'] = datetime.now().isoformat()
                    session.permanent = True
                    app.permanent_session_lifetime = timedelta(hours=2)
                    
                    logger.info(f"✓ Admin login exitoso: {usuario} desde {request.remote_addr}")
                    registrar_audit('LOGIN_ADMIN', usuario, None, 'Login exitoso', request.remote_addr)
                    flash('✓ Sesión iniciada correctamente', 'success')
                    return redirect(url_for('admin_dashboard'))
                else:
                    logger.warning(f"❌ Intento login fallido: {usuario} desde {request.remote_addr}")
                    registrar_audit('LOGIN_FALLIDA', usuario, None, 'Contraseña incorrecta', request.remote_addr)
                    flash('❌ Usuario o contraseña incorrectos', 'error')
            except Exception as e:
                logger.error(f"Error verificando contraseña: {e}")
                flash('❌ Error en autenticación', 'error')
        else:
            logger.warning(f"❌ Intento login con usuario no existente: {usuario}")
            flash('❌ Usuario o contraseña incorrectos', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged', None)
    session.pop('admin_user', None)
    flash('✓ Sesión cerrada correctamente', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged') == True:
        flash('⚠️ Acceso denegado. Por favor ingresa con tus credenciales.', 'error')
        return redirect(url_for('admin'))
    
    try:
        conn = get_db()
        pendientes = conn.execute("SELECT * FROM reservas WHERE estado='pendiente' ORDER BY fecha_evento ASC").fetchall()
        confirmadas = conn.execute("SELECT * FROM reservas WHERE estado='confirmada' ORDER BY fecha_evento DESC").fetchall()
        canceladas = conn.execute("SELECT * FROM reservas WHERE estado='cancelada' ORDER BY fecha_evento DESC").fetchall()
        total = conn.execute("SELECT COUNT(*) as count FROM reservas").fetchone()

        # Estadísticas
        from datetime import date
        mes_actual = date.today().strftime('%Y-%m')
        stats_tipo = conn.execute("""
            SELECT mensaje, COUNT(*) as total FROM reservas 
            WHERE estado='confirmada' GROUP BY 
            CASE 
                WHEN mensaje LIKE '%privado_ibague%' THEN 'Privado Ibague'
                WHEN mensaje LIKE '%privado_fuera%' THEN 'Privado Fuera'
                WHEN mensaje LIKE '%masivo_ibague%' THEN 'Masivo Ibague'
                WHEN mensaje LIKE '%masivo_fuera%' THEN 'Masivo Fuera'
                ELSE 'Otro'
            END
        """).fetchall()

        conn.close()
        return render_template('admin_dashboard.html',
                             pendientes=pendientes,
                             confirmadas=confirmadas,
                             canceladas=canceladas,
                             total=total['count'],
                             stats_tipo=stats_tipo,
                             mes_actual=mes_actual)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin'))

@app.route('/admin/confirmar/<int:id>')
def admin_confirmar(id):
    if not session.get('admin_logged'):
        flash('⚠️ Acceso denegado. Inicia sesión nuevamente.', 'error')
        return redirect(url_for('admin'))
    
    try:
        conn = get_db()
        reserva = conn.execute("SELECT * FROM reservas WHERE id=?", (id,)).fetchone()
        
        if reserva:
            # Actualizar estado
            conn.execute("UPDATE reservas SET estado='confirmada', actualizado=datetime('now') WHERE id=?", (id,))
            conn.commit()
            
            # Enviar correo en background (no bloquea el worker)
            try:
                enviar_confirmacion_async(reserva)
                envio_exitoso = True
            except Exception as mail_err:
                logger.error(f"Error en enviar_confirmacion: {mail_err}")
                envio_exitoso = False

            # Notificación WhatsApp (link para enviar manualmente)
            wa_msg = f"Hola {reserva['nombre']}, tu reserva con Herencia de Acero para el {reserva['fecha_evento']} a las {reserva['hora_evento']} ha sido CONFIRMADA. ¡Nos vemos pronto!"
            from urllib.parse import quote
            wa_link = f"https://wa.me/{reserva['telefono'].replace(' ','').replace('+','')}?text={quote(wa_msg)}"
            
            # Registrar en auditoría
            registrar_audit('CONFIRMAR_RESERVA', session.get('admin_user'), id, f"Confirmada {reserva['nombre']}", request.remote_addr)
            
            if envio_exitoso:
                logger.info(f"Reserva confirmada y correo enviado: ID={id}")
                flash(f'✓ Reserva de {reserva["nombre"]} confirmada y correo enviado | <a href="{wa_link}" target="_blank" style="color:#25D366;">📱 Enviar WhatsApp</a>', 'success')
            else:
                logger.warning(f"Reserva confirmada pero correo falló: ID={id}")
                flash(f'✓ Reserva de {reserva["nombre"]} confirmada | <a href="{wa_link}" target="_blank" style="color:#25D366;">📱 Enviar WhatsApp</a>', 'warning')
        
        conn.close()
    except Exception as e:
        logger.error(f"Error confirmando reserva: {e}")
        flash(f'❌ Error: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/eliminar/<int:id>')
def admin_eliminar(id):
    if not session.get('admin_logged'):
        flash('⚠️ Acceso denegado. Inicia sesión nuevamente.', 'error')
        return redirect(url_for('admin'))
    
    conn = get_db()
    reserva = conn.execute("SELECT * FROM reservas WHERE id=?", (id,)).fetchone()
    
    if reserva:
        conn.execute("DELETE FROM reservas WHERE id=?", (id,))
        conn.commit()
        flash(f'✓ Reserva de {reserva["nombre"]} eliminada correctamente', 'success')
    
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/cancelar/<int:id>')
def admin_cancelar(id):
    if not session.get('admin_logged'):
        return redirect(url_for('admin'))
    conn = get_db()
    reserva = conn.execute("SELECT * FROM reservas WHERE id=?", (id,)).fetchone()
    if reserva:
        conn.execute("UPDATE reservas SET estado='cancelada' WHERE id=?", (id,))
        conn.commit()
        flash(f'✓ Reserva de {reserva["nombre"]} cancelada', 'warning')
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/exportar')
def admin_exportar():
    if not session.get('admin_logged'):
        return redirect(url_for('admin'))
    import csv, io
    from flask import Response
    conn = get_db()
    reservas = conn.execute("SELECT * FROM reservas ORDER BY fecha_evento DESC").fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID','Nombre','Email','Telefono','Fecha','Hora','Detalles','Estado','Creado','Actualizado'])
    for r in reservas:
        writer.writerow([r['id'],r['nombre'],r['email'],r['telefono'],r['fecha_evento'],r['hora_evento'],r['mensaje'],r['estado'],r['creado'],r['actualizado']])
    output.seek(0)
    return Response(output, mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment;filename=reservas.csv'})

@app.route('/admin/exportar-pdf')
def admin_exportar_pdf():
    if not session.get('admin_logged'):
        return redirect(url_for('admin'))
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        import io
        
        conn = get_db()
        reservas = conn.execute("SELECT * FROM reservas ORDER BY fecha_evento DESC").fetchall()
        confirmadas = conn.execute("SELECT COUNT(*) as count FROM reservas WHERE estado='confirmada'").fetchone()['count']
        pendientes = conn.execute("SELECT COUNT(*) as count FROM reservas WHERE estado='pendiente'").fetchone()['count']
        total = conn.execute("SELECT COUNT(*) as count FROM reservas").fetchone()['count']
        conn.close()
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#d4af37'), spaceAfter=6, alignment=1)
        elements.append(Paragraph("HERENCIA DE ACERO", title_style))
        elements.append(Paragraph("Reporte de Reservas", styles['Heading2']))
        elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Estadísticas
        stats_data = [
            ['Total Reservas', f'{total}'],
            ['Confirmadas', f'{confirmadas}'],
            ['Pendientes', f'{pendientes}']
        ]
        stats_table = Table(stats_data, colWidths=[3*inch, 1.5*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Tabla de reservas
        table_data = [['ID', 'Nombre', 'Email', 'Teléfono', 'Fecha', 'Hora', 'Estado']]
        for r in reservas:
            table_data.append([
                str(r['id']),
                r['nombre'][:30],
                r['email'][:25],
                r['telefono'][:15],
                r['fecha_evento'],
                r['hora_evento'],
                r['estado'].upper()
            ])
        
        table = Table(table_data, colWidths=[0.6*inch, 1.5*inch, 1.5*inch, 1*inch, 1*inch, 0.7*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d4af37')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        elements.append(table)
        
        doc.build(elements)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f"reservas_{datetime.now().strftime('%d%m%Y')}.pdf", mimetype='application/pdf')
    except ImportError:
        logger.warning("reportlab no instalado, usando CSV en su lugar")
        return admin_exportar()
    except Exception as e:
        logger.error(f"Error generando PDF: {e}")
        flash('Error generando PDF', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/enviar_testimonio', methods=['POST'])
@limiter.limit("5 per hour")
def enviar_testimonio():
    """Guardar testimonio enviado por cliente"""
    try:
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        tipo_evento = request.form.get('tipo_evento', '').strip()
        calificacion = request.form.get('calificacion', 5)
        comentario = request.form.get('comentario', '').strip()
        
        # Validaciones
        if not validar_nombre(nombre):
            return {'success': False, 'message': 'Nombre inválido'}, 400
        if not validar_email(email):
            return {'success': False, 'message': 'Email inválido'}, 400
        if not comentario or len(comentario) < 10:
            return {'success': False, 'message': 'Comentario muy corto (mínimo 10 caracteres)'}, 400
        
        try:
            calificacion = int(calificacion)
            if calificacion < 1 or calificacion > 5:
                calificacion = 5
        except:
            calificacion = 5
        
        # Guardar en BD
        conn = get_db()
        conn.execute("""
            INSERT INTO testimonios 
            (nombre, email, tipo_evento, calificacion, comentario, estado)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nombre, email, tipo_evento, calificacion, comentario, 'pendiente'))
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Testimonio recibido de {nombre} ({email})")
        return {'success': True, 'message': '¡Gracias por tu testimonio! Será revisado pronto.'}, 200
        
    except Exception as e:
        logger.error(f"Error al guardar testimonio: {e}")
        return {'success': False, 'message': 'Error al procesar tu solicitud'}, 500

@app.route('/admin/testimonios')
def admin_testimonios():
    """Panel de administración de testimonios"""
    if not session.get('admin_logged'):
        return redirect(url_for('admin'))
    try:
        conn = get_db()
        testimonios_pendientes = conn.execute("""
            SELECT id, nombre, email, tipo_evento, calificacion, comentario, creado 
            FROM testimonios 
            WHERE estado = 'pendiente' 
            ORDER BY creado DESC
        """).fetchall()
        
        testimonios_aprobados = conn.execute("""
            SELECT id, nombre, email, tipo_evento, calificacion, comentario, aprobado 
            FROM testimonios 
            WHERE estado = 'aprobado' 
            ORDER BY aprobado DESC 
            LIMIT 20
        """).fetchall()
        
        conn.close()
        return render_template('admin_testimonios.html', 
                             testimonios_pendientes=testimonios_pendientes,
                             testimonios_aprobados=testimonios_aprobados)
    except Exception as e:
        logger.error(f"Error cargando testimonios admin: {e}")
        flash('Error cargando testimonios', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/aprobar_testimonio/<int:id>', methods=['POST'])
def admin_aprobar_testimonio(id):
    """Aprobar un testimonio"""
    if not session.get('admin_logged'):
        return {'success': False}, 401
    try:
        conn = get_db()
        conn.execute("""
            UPDATE testimonios 
            SET estado = 'aprobado', aprobado = datetime('now')
            WHERE id = ?
        """, (id,))
        conn.commit()
        conn.close()
        
        registrar_audit('TESTIMONIO_APROBADO', session.get('admin_user', 'admin'), id, f'Testimonio #{id} aprobado', request.remote_addr)
        logger.info(f"✅ Testimonio #{id} aprobado")
        return {'success': True, 'message': 'Testimonio aprobado'}, 200
    except Exception as e:
        logger.error(f"Error aprobando testimonio: {e}")
        return {'success': False, 'message': 'Error aprobando testimonio'}, 500

@app.route('/admin/rechazar_testimonio/<int:id>', methods=['POST'])
def admin_rechazar_testimonio(id):
    """Rechazar un testimonio"""
    if not session.get('admin_logged'):
        return {'success': False}, 401
    try:
        conn = get_db()
        conn.execute("""
            DELETE FROM testimonios 
            WHERE id = ?
        """, (id,))
        conn.commit()
        conn.close()
        
        registrar_audit('TESTIMONIO_RECHAZADO', session.get('admin_user', 'admin'), id, f'Testimonio #{id} rechazado', request.remote_addr)
        logger.info(f"✅ Testimonio #{id} rechazado")
        return {'success': True, 'message': 'Testimonio rechazado'}, 200
    except Exception as e:
        logger.error(f"Error rechazando testimonio: {e}")
        return {'success': False, 'message': 'Error rechazando testimonio'}, 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    app.run(host=host, port=port, debug=app.config.get('DEBUG', False))
