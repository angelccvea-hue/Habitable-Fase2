"""
Django settings — CPEH Fase II (UI: Jazzmin + WhiteNoise).
"""
from pathlib import Path
import os

from dotenv import load_dotenv

from .jazzmin_settings import JAZZMIN_SETTINGS, JAZZMIN_UI_TWEAKS

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-change-me")
DEBUG = os.environ.get("DEBUG", "1") == "1"
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.forms",  # plantillas de widgets (attrs.html) con FORM_RENDERER TemplatesSetting
    "rest_framework",
    "corsheaders",
    "inspecciones",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# Necesario para que widgets custom (p. ej. evidencias) usen plantillas del proyecto
# en templates/django/forms/widgets/…; sin esto Django solo mira las del paquete forms.
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

if os.environ.get("DATABASE_ENGINE", "sqlite") == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "fase2_rojo"),
            "USER": os.environ.get("DB_USER", "fase2_app"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-ve"
TIME_ZONE = "America/Caracas"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        # Manifest estricto rompe el admin Jazzmin (refs a carpetas tipo vendor/bootswatch).
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Por si se vuelve a Manifest en el futuro
WHITENOISE_MANIFEST_STRICT = False

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Despliegue acotado: menú/rutas hasta mapa (sin visor metrados PLN-01 / MET-01 detallado).
CPEH_SCOPE_HASTA_MAPA = os.environ.get("CPEH_SCOPE_HASTA_MAPA", "0") == "1"

# Ficha CasoRojo + varios inlines (metrados, fotos, PDF, croquis) puede superar
# el default de Django (1000). Si se trunca el POST, «Guardar y continuar editando»
# parece borrar secciones llenadas (campos ausentes llegan vacíos).
DATA_UPLOAD_MAX_NUMBER_FIELDS = int(os.environ.get("DATA_UPLOAD_MAX_NUMBER_FIELDS", "20000"))
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get("DATA_UPLOAD_MAX_MEMORY_SIZE", str(50 * 1024 * 1024)))

# Sin esto, las excepciones 500 no quedan en nohup (LOGGING={} desactiva el default).
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file_500": {
            "class": "logging.FileHandler",
            "filename": str(BASE_DIR / "logs" / "django_errors.log"),
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["console", "file_500"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console", "file_500"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

JAZZMIN_SETTINGS = JAZZMIN_SETTINGS
JAZZMIN_UI_TWEAKS = JAZZMIN_UI_TWEAKS

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}

CORS_ALLOW_ALL_ORIGINS = DEBUG

# Detrás de proxy (Nginx) — hosts HTTP explícitos
_csrf = os.environ.get("CSRF_TRUSTED_ORIGINS", "").strip()
if _csrf:
    CSRF_TRUSTED_ORIGINS = [h.strip() for h in _csrf.split(",") if h.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [
        f"http://{h}" for h in ALLOWED_HOSTS if h not in ("*", "localhost", "127.0.0.1")
    ] + ["http://localhost", "http://127.0.0.1"]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Guía PDF usuario: False = marca «BORRADOR EN REVISIÓN» hasta aprobación gerencial
GUIA_USUARIO_PDF_APROBADA = os.environ.get("GUIA_USUARIO_PDF_APROBADA", "0") == "1"
