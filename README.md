# Herencia de Acero - Sitio Web

Agrupación musical de banda para eventos en Ibagué y fuera.

## 🚀 Despliegue en Heroku

1. **Sube el código a GitHub**:
   - Crea un repo en GitHub.
   - Sube todos los archivos (excepto .env si contiene secrets reales).

2. **Crea app en Heroku**:
   - Ve a heroku.com, crea cuenta.
   - Crea nueva app, conecta a tu repo de GitHub.

3. **Configura variables de entorno**:
   - En Heroku Dashboard > Settings > Config Vars, agrega:
     - `FLASK_ENV`: production
     - `SECRET_KEY`: (genera uno nuevo seguro)
     - `MAIL_USERNAME`: tu email
     - `MAIL_PASSWORD`: app password
     - `ADMIN_USER`: admin
     - `ADMIN_PASSWORD_HASH`: (el hash generado)
     - `DATABASE_NAME`: reservas.db
     - `DEBUG`: False

4. **Despliega**:
   - En Heroku, habilita auto-deploy o despliega manualmente.
   - El sitio estará en https://tu-app.herokuapp.com

## 🧪 Pruebas Locales

- Ejecuta: `python app.py`
- Abre http://127.0.0.1:5000
- Prueba: reservas, testimonios, admin (/admin con user: admin, pass: herencia2026)

## 📋 Checklist Final

- [ ] App corre sin errores
- [ ] Formularios funcionan
- [ ] Emails se envían
- [ ] Admin panel accesible
- [ ] Responsive en móvil
- [ ] Imágenes optimizadas

¡Listo para rockear! 🎸