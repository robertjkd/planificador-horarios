"""
Django settings for planificador project.
"""
import os
from pathlib import Path
import environ

# Inicializar django-environ
env = environ.Env(
    # Establecer valores por defecto
    DEBUG=(bool, False),
    DB_ENGINE=(str, 'sqlite'),  # 'sqlite' o 'postgresql'
    DB_NAME=(str, 'db.sqlite3'),
    DB_USER=(str, 'postgres'),
    DB_PASSWORD=(str, ''),
    DB_HOST=(str, 'localhost'),
    DB_PORT=(str, '5432'),
    SECRET_KEY=(str, 'django-insecure-change-me-in-production'),
)

# Leer archivo .env si existe
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')

DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Local apps
    'usuarios',
    'academico',
    'horario',
    'planificacion',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'planificador.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'planificador.wsgi.application'

# ─────────────────────────────────────────────────────────────
# CONFIGURACIÓN DINÁMICA DE BASE DE DATOS
# ─────────────────────────────────────────────────────────────
DB_ENGINE = env('DB_ENGINE')  # 'sqlite' o 'postgresql'

if DB_ENGINE == 'postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('DB_NAME'),
            'USER': env('DB_USER'),
            'PASSWORD': env('DB_PASSWORD'),
            'HOST': env('DB_HOST'),
            'PORT': env('DB_PORT'),
        }
    }
else:
    # SQLite como fallback para desarrollo
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / env('DB_NAME'),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ('username', 'email', 'first_name', 'last_name'),
        }
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

AUTH_USER_MODEL = 'usuarios.Usuario'

LANGUAGE_CODE = 'es'

TIME_ZONE = 'America/Havana'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# ─────────────────────────────────────────────────────────────
# LOGGING CONFIGURATION
# ─────────────────────────────────────────────────────────────
import os

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
        'auditoria': {
            'format': '{asctime} | {levelname} | {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'app.log'),
            'maxBytes': 5 * 1024 * 1024,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'auditoria_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'auditoria.log'),
            'maxBytes': 5 * 1024 * 1024,  # 5 MB
            'backupCount': 5,
            'formatter': 'auditoria',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'auditoria': {
            'handlers': ['auditoria_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Crear directorio de logs si no existe
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# ─────────────────────────────────────────────────────────────
# EMAIL CONFIGURATION (para alertas de fallos del solver)
# ─────────────────────────────────────────────────────────────
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@planificador.edu')
ADMINS = [
    ('Vicedecano', env('ADMIN_EMAIL', default='vicedecano@planificador.edu')),
]

# Umbral de fallos del solver para enviar alerta (en la última hora)
SOLVER_FAILURE_THRESHOLD = env('SOLVER_FAILURE_THRESHOLD', default=3, cast=int)
SOLVER_FAILURE_WINDOW_HOURS = env('SOLVER_FAILURE_WINDOW_HOURS', default=1, cast=int)

# ─────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE VALIDACIÓN DE EMAIL Y USUARIOS
# ─────────────────────────────────────────────────────────────

# Dominios de correo electrónico permitidos para registro de usuarios
EMAIL_DOMINIOS_PERMITIDOS = env.list(
    'EMAIL_DOMINIOS_PERMITIDOS',
    default=['gmail.com', 'uci.cu']
)

# Configuración de validación de contraseñas genéricas
PASSWORD_GENERICO_PREFIX_LENGTH = 3  # Primeras N letras del nombre para password genérico
PASSWORD_GENERICO_SUFFIX = '123456'  # Sufijo para password genérico

# Validación de nombres de usuario
USERNAME_MAX_LENGTH = 150
USERNAME_REGEX = r'^[\w.@+-]+$'  # Letras, dígitos, @, ., +, -, _
