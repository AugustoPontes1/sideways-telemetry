"""Configurações. SQLite / memória apenas no ambiente local; PostgreSQL/Redis em produção."""
from __future__ import annotations

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in ("1", "true", "yes", "on")


DEBUG = env_bool("DJANGO_DEBUG", True)
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "development-only-not-for-deployment-change-this-secret"
    else:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY é obrigatório em produção")

ALLOWED_HOSTS = [h.strip() for h in os.getenv(
    "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]"
).split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [url.strip() for url in os.getenv(
    "DJANGO_CSRF_TRUSTED_ORIGINS", ""
).split(",") if url.strip()]

TELEMETRY_TOKEN = os.getenv("TELEMETRY_TOKEN", "")
TELEMETRY_AGENT_ID = os.getenv("TELEMETRY_AGENT_ID", "wsl-assetto-agent")
if not DEBUG and len(TELEMETRY_TOKEN) < 32:
    raise ImproperlyConfigured("Configure TELEMETRY_TOKEN seguro, com pelo menos 32 caracteres")
if not TELEMETRY_AGENT_ID or len(TELEMETRY_AGENT_ID) > 100:
    raise ImproperlyConfigured("TELEMETRY_AGENT_ID inválido")

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "channels",
    "sessions",
    "telemetry",
    "analysis",
    "learning",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
ASGI_APPLICATION = "config.asgi.application"
WSGI_APPLICATION = "config.wsgi.application"

if os.getenv("DATABASE_ENGINE", "sqlite").lower() == "postgresql":
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "drift_telemetry"),
        "USER": os.getenv("POSTGRES_USER", "drift"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
        "HOST": os.getenv("POSTGRES_HOST", "db"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 0,  # evitar conexões persistentes no executor async
    }}
else:
    if not DEBUG:
        raise ImproperlyConfigured("Produção requer DATABASE_ENGINE=postgresql")
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.getenv("DJANGO_SQLITE_PATH", str(BASE_DIR / "dev.sqlite3")),
    }}

redis_url = os.getenv("REDIS_URL", "").strip()
if redis_url:
    CHANNEL_LAYERS = {"default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [redis_url]},
    }}
else:
    if not DEBUG:
        raise ImproperlyConfigured("Produção requer REDIS_URL")
    CHANNEL_LAYERS = {"default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAdminUser"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Ativar somente atrás de proxy reverso que remove e define X-Forwarded-Proto.
if env_bool("DJANGO_TRUST_PROXY_PROTO"):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", False)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"short": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "short"}},
    "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "INFO")},
}


# Trusted frontend origin for local Vite development
CSRF_TRUSTED_ORIGINS = [
    *CSRF_TRUSTED_ORIGINS,
    "http://127.0.0.1:5173",
]
