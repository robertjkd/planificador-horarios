# Recomendaciones de Seguridad - Planificador de Horarios Académicos

Este documento detalla las recomendaciones de seguridad específicas para el sistema de planificación de horarios académicos basado en Django 5.0.4.

## 1. Control de Acceso Basado en Roles (RBAC)

### Implementación Actual
- **Modelo Usuario**: Campo `rol` con choices (VICEDECANO, PLANIFICADOR, CONSULTA)
- **Decorador `@rol_requerido`**: Para vistas basadas en funciones
- **Mixin `RolesRequeridosMixin`**: Para vistas basadas en clases
- **Protección contra escalada de privilegios**: Vicedecano no puede crear otros Vicedecanos

### Buenas Prácticas Adicionales

#### 1.1 Validación de Permisos en Formularios
```python
# En usuarios/forms.py, validar que el rol no sea VICEDECANO
class UsuarioCreationForm(forms.ModelForm):
    def clean_rol(self):
        rol = self.cleaned_data['rol']
        if rol == Usuario.Rol.VICEDECANO:
            raise forms.ValidationError('No se puede crear otro usuario con rol Vicedecano.')
        return rol
```

#### 1.2 Uso de get_object_or_404
Siempre usar `get_object_or_404` en lugar de `get()` con try/except para evitar divulgación de información:
```python
# ✅ Correcto
usuario = get_object_or_404(Usuario, pk=pk)

# ❌ Incorrecto
try:
    usuario = Usuario.objects.get(pk=pk)
except Usuario.DoesNotExist:
    return HttpResponse('Usuario no encontrado', status=404)
```

#### 1.3 No Exponer IDs en URLs Innecesariamente
Para vistas de consulta, usar slugs o códigos en lugar de IDs numéricos cuando sea posible:
```python
# ✅ Mejor
path('horario/<slug:anio_codigo>/<int:semana>/', views.ver_horario)

# ⚠️ Aceptable pero menos seguro
path('horario/<int:anio_id>/<int:semana>/', views.ver_horario)
```

## 2. Protección CSRF, XSS, SQL Injection

### 2.1 CSRF (Cross-Site Request Forgery)
Django incluye protección CSRF por defecto. Asegurar que:
- Todos los formularios POST incluyan `{% csrf_token %}`
- Las vistas API usen `@csrf_exempt` solo cuando sea absolutamente necesario
- Configurar `CSRF_COOKIE_SECURE = True` en producción

```python
# En settings.py (producción)
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
```

### 2.2 XSS (Cross-Site Scripting)
Django escapa HTML automáticamente en templates. Precauciones adicionales:
- Nunca usar `|safe` con datos de usuario no confiables
- Para contenido HTML permitido, usar `bleach` para sanitizar:
```python
import bleach

def limpiar_html(texto):
    return bleach.clean(texto, tags=['b', 'i', 'u'], strip=True)
```

### 2.3 SQL Injection
Django ORM protege contra SQL injection. Reglas:
- Siempre usar el ORM, nunca concatenar strings para queries
- Para queries complejos, usar `raw()` con parámetros:
```python
# ✅ Correcto
Usuario.objects.raw('SELECT * FROM usuarios_usuario WHERE rol = %s', [rol])

# ❌ Incorrecto
Usuario.objects.raw(f'SELECT * FROM usuarios_usuario WHERE rol = {rol}')
```

## 3. Contraseñas y Política de Usuarios

### 3.1 Almacenamiento Seguro
Django almacena contraseñas hasheadas automáticamente usando PBKDF2. Configuración recomendada:
```python
# settings.py
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

### 3.2 Forzar Cambio de Contraseña
Implementar campo `debe_cambiar_password` en Usuario:
```python
# usuarios/models.py
class Usuario(AbstractUser):
    debe_cambiar_password = models.BooleanField(default=True)
    
    def check_password_change_required(self):
        if self.debe_cambiar_password:
            return redirect('cambiar_password')
```

### 3.3 No Mostrar Contraseñas
Nunca mostrar contraseñas en texto plano en logs, emails o interfaces:
```python
# ❌ Incorrecto
logger.info(f'Usuario creado: {username}, password: {password}')

# ✅ Correcto
logger.info(f'Usuario creado: {username}')
```

## 4. Protección de Archivos

### 4.1 Validación de Archivos Subidos
En `ImportarBalanceForm`, ya se valida tipo y tamaño. Validaciones adicionales:
```python
# planificacion/forms.py
class ImportarBalanceForm(forms.Form):
    archivo = forms.FileField()
    
    def clean_archivo(self):
        archivo = self.cleaned_data['archivo']
        
        # Validar extensión
        ext = archivo.name.split('.')[-1].lower()
        if ext not in ['csv', 'xlsx']:
            raise forms.ValidationError('Solo se permiten archivos CSV y Excel.')
        
        # Validar tamaño (5 MB máximo)
        if archivo.size > 5 * 1024 * 1024:
            raise forms.ValidationError('El archivo no puede superar 5 MB.')
        
        # Validar magic bytes (contenido real del archivo)
        archivo.seek(0)
        header = archivo.read(8)
        archivo.seek(0)
        
        if ext == 'xlsx' and not header.startswith(b'PK\x03\x04'):
            raise forms.ValidationError('El archivo no es un Excel válido.')
        
        return archivo
```

### 4.2 Almacenamiento Temporal
Eliminar archivos después del procesamiento:
```python
import os
import tempfile

def procesar_archivo(archivo):
    # Crear archivo temporal
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        for chunk in archivo.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name
    
    try:
        # Procesar archivo
        resultado = procesar(tmp_path)
    finally:
        # Siempre eliminar archivo temporal
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    
    return resultado
```

### 4.3 No Accesibles Públicamente
Configurar MEDIA_ROOT fuera del directorio público:
```python
# settings.py
MEDIA_ROOT = os.path.join(BASE_DIR, 'media_privado')
MEDIA_URL = '/media-privado/'
```

## 5. Sesiones y Expiración

### 5.1 Configuración de Sesiones
```python
# settings.py
SESSION_COOKIE_AGE = 3600  # 1 hora
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
```

### 5.2 Cierre de Sesión
Asegurar que logout destruya la sesión completamente:
```python
# usuarios/views.py
from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    # Limpiar datos de sesión adicionales
    request.session.flush()
    return redirect('login')
```

## 6. Auditoría

### 6.1 Modelo de Auditoría
```python
# academico/models.py
class Auditoria(models.Model):
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True)
    accion = models.CharField(max_length=100)
    fecha = models.DateTimeField(auto_now_add=True)
    detalles = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True)
    
    class Meta:
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'
        ordering = ['-fecha']
```

### 6.2 Registro de Acciones Críticas
```python
# Decorador para registrar acciones
from functools import wraps

def auditar(accion):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            resultado = view_func(request, *args, **kwargs)
            
            # Registrar solo acciones críticas
            if request.method == 'POST':
                Auditoria.objects.create(
                    usuario=request.user,
                    accion=accion,
                    detalles={
                        'path': request.path,
                        'method': request.method,
                        'params': dict(request.POST),
                    },
                    ip_address=get_client_ip(request),
                )
            
            return resultado
        return _wrapped_view
    return decorator

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
```

### 6.3 Acciones a Auditar
- Creación/eliminación de usuarios
- Importación de balances
- Generación de horarios
- Modificación manual de asignaciones

## 7. Protección Contra Fuerza Bruta

### 7.1 Django Axes
Instalar y configurar django-axes:
```bash
pip install django-axes
```

```python
# settings.py
INSTALLED_APPS = [
    ...
    'axes',
]

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hora
AXES_LOCKOUT_TEMPLATE = 'axes_locked.html'
```

```python
# urls.py
urlpatterns = [
    path('', include('axes.urls')),
    ...
]
```

## 8. HTTPS en Producción

### 8.1 Configuración SSL
```python
# settings.py (producción)
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

### 8.2 Cookies Seguras
```python
# settings.py (producción)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## 9. Validación de Datos de Entrada

### 9.1 Sanitización de Inputs
```python
# Siempre validar y limpiar datos de usuario
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

def validar_email(email):
    try:
        validate_email(email)
        return email.lower().strip()
    except ValidationError:
        raise ValueError('Email inválido')
```

### 9.2 Validación de IDs
```python
# Validar que el ID pertenezca al usuario antes de acceder
def ver_mi_perfil(request, usuario_id):
    if request.user.rol != 'VICEDECANO' and request.user.pk != usuario_id:
        raise PermissionDenied('No tiene permiso para ver este perfil.')
    ...
```

## 10. Logs y Monitoreo

### 10.1 Configuración de Logging
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/security.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}
```

### 10.2 Eventos a Registrar
- Intentos de login fallidos
- Acciones de Vicedecano
- Errores de permisos
- Subida de archivos
- Cambios en configuración

## 11. Protección de API (Futuro)

### 11.1 Django REST Framework
Si se implementa API REST:
```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    }
}
```

### 11.2 Permisos Personalizados
```python
# permissions.py
from rest_framework import permissions

class EsVicedecano(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.rol == 'VICEDECANO'
```

## 12. Resumen de Checklist de Seguridad

### Antes de Desplegar a Producción
- [ ] Configurar HTTPS con certificado SSL válido
- [ ] Habilitar `SECURE_SSL_REDIRECT`
- [ ] Configurar cookies seguras (`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`)
- [ ] Instalar y configurar django-axes
- [ ] Configurar logging de seguridad
- [ ] Implementar modelo de auditoría
- [ ] Validar que no se puedan crear Vicedecanos adicionales
- [ ] Revisar todas las vistas con `@login_required` o decoradores de rol
- [ ] Configurar `DEBUG = False`
- [ ] Usar variables de entorno para datos sensibles
- [ ] Implementar validación de archivos subidos
- [ ] Configurar política de contraseñas robusta
- [ ] Revisar permisos de archivos en servidor
- [ ] Configurar firewall para restringir acceso
- [ ] Implementar backups automatizados
- [ ] Configurar monitoreo de errores

### Mantenimiento Continuo
- [ ] Revisar logs de seguridad regularmente
- [ ] Actualizar dependencias (Django, paquetes Python)
- [ ] Realizar auditorías de permisos periódicamente
- [ ] Revisar registros de auditoría
- [ ] Probar recuperación de desastres
- [ ] Capacitar a usuarios sobre seguridad (phishing, contraseñas)
