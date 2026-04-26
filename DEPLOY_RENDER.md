# 🚀 Guía de Despliegue en Render.com

Esta guía te ayudará a desplegar el Planificador de Horarios en Render.com

---

## ✅ Resumen de Cambios Realizados

### 1. requirements.txt
Añadidas dependencias de producción:
```
gunicorn==23.0.0
dj-database-url==2.1.0
whitenoise==6.6.0
```

### 2. planificador/settings.py
- ✅ Import `dj_database_url`
- ✅ Whitenoise middleware añadido
- ✅ Configuración de base de datos con `DATABASE_URL`
- ✅ Static files con whitenoise
- ✅ Configuración de seguridad para producción

### 3. build.sh
Script de construcción creado para Render

---

## 📋 Pasos para Desplegar en Render

### Paso 1: Crear Repositorio en GitHub

```bash
# En tu proyecto local
git init
git add .
git commit -m "Configuración para producción en Render"

# Crear repositorio en GitHub y subir
git remote add origin https://github.com/TU_USUARIO/planificador-horarios.git
git branch -M main
git push -u origin main
```

---

### Paso 2: Crear Web Service en Render

1. Ve a [render.com](https://render.com) e inicia sesión
2. Click en **"New +"** → **"Web Service"**
3. Conecta tu repositorio de GitHub
4. Configura:

| Campo | Valor |
|-------|-------|
| **Name** | planificador-horarios |
| **Region** | Oregon (US West) |
| **Runtime** | Python 3 |
| **Build Command** | `./build.sh` |
| **Start Command** | `gunicorn planificador.wsgi:application --bind 0.0.0.0:$PORT` |

---

### Paso 3: Configurar Variables de Entorno

En el dashboard de Render, ve a **Environment** y añade:

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `SECRET_KEY` | `tu-clave-secreta-generada` | Genera con: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `False` | Modo producción |
| `ALLOWED_HOSTS` | `planificador-horarios.onrender.com` | Tu dominio de Render |

**NOTA:** No necesitas configurar `DATABASE_URL` manualmente - Render la genera automáticamente al crear la base de datos PostgreSQL.

---

### Paso 4: Crear Base de Datos PostgreSQL

1. En Render, click en **"New +"** → **"PostgreSQL"**
2. Configura:
   - **Name:** planificador-db
   - **Region:** Oregon (US West) - debe coincidir con tu web service
   - **Plan:** Free (o el que prefieras)
3. Click **Create Database**
4. Espera a que se cree (1-2 minutos)

**Render conectará automáticamente la base de datos a tu web service** y creará la variable `DATABASE_URL`.

---

### Paso 5: Desplegar

1. Vuelve a tu **Web Service**
2. Click en **Manual Deploy** → **Deploy latest commit**
3. Render ejecutará `build.sh` automáticamente:
   - Instalará dependencias
   - Recopilará estáticos
   - Aplicará migraciones
4. Espera a que termine (2-3 minutos)

---

## 🔧 Comandos Útiles para Render

### Ver Logs
En el dashboard de Render → tu web service → **Logs**

### Shell (comandos de Django)
En el dashboard → **Shell**:

```bash
# Crear superusuario
python manage.py createsuperuser

# Verificar estado
python manage.py check

# Ejecutar migraciones manuales
python manage.py migrate
```

---

## 🛠️ Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'dj_database_url'"
**Solución:** Asegúrate de que `build.sh` tenga permisos de ejecución y que `requirements.txt` incluya `dj-database-url`.

### Error: "Static files not found"
**Solución:** Verifica que `build.sh` ejecute `collectstatic` y que `STATIC_ROOT` esté configurado.

### Error: "Database connection failed"
**Solución:** Asegúrate de haber creado la base de datos PostgreSQL y que esté en la misma región que el web service.

### Error: "DisallowedHost"
**Solución:** Agrega tu dominio de Render a la variable `ALLOWED_HOSTS`.

---

## 📁 Estructura de Archivos para Producción

```
planificador-horarios/
├── build.sh                  # Script de construcción
├── requirements.txt          # Dependencias
├── .env.example              # Ejemplo de variables
├── .gitignore               # Archivos ignorados
├── planificador/
│   ├── settings.py          # Configuración actualizada
│   ├── wsgi.py              # Punto de entrada
│   └── urls.py              # URLs
├── static/                   # Archivos estáticos
├── staticfiles/             # Generado por collectstatic
├── mediafiles/              # Archivos subidos (no persistente en Render)
└── manage.py
```

---

## 🔒 Consideraciones de Seguridad

1. **SECRET_KEY:** Nunca la expongas en el código, usa variables de entorno
2. **DEBUG:** Siempre `False` en producción
3. **ALLOWED_HOSTS:** Especifica solo tus dominios
4. **MEDIA FILES:** En Render Free, los archivos subidos se pierden al reiniciar. Para producción real, usa Cloudinary o AWS S3.

---

## 📝 Checklist Pre-Deploy

- [ ] `requirements.txt` incluye gunicorn, dj-database-url, whitenoise
- [ ] `settings.py` importa `dj_database_url`
- [ ] Whitenoise middleware está en `MIDDLEWARE`
- [ ] `build.sh` existe y tiene contenido correcto
- [ ] Variables de entorno configuradas en Render
- [ ] Base de datos PostgreSQL creada en Render
- [ ] Código subido a GitHub
- [ ] Repositorio conectado a Render

---

## 🎯 URLs de tu Aplicación en Producción

Una vez desplegado, tu app estará disponible en:

```
https://planificador-horarios.onrender.com
```

---

## 📞 Soporte

Si tienes problemas:
1. Revisa los **Logs** en el dashboard de Render
2. Verifica que las variables de entorno estén correctas
3. Asegúrate de que la base de datos esté conectada

¡Listo para desplegar! 🚀
