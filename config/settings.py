import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# DJANGO_ENV = os.getenv("DJANGO_ENV", "dev").lower()
# env_file = BASE_DIR / (".env.dev" if DJANGO_ENV == "dev" else ".env.prod")
# if env_file.exists():
load_dotenv(".env.dev")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "*").split(",") if h.strip()]

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://b371-144-124-192-132.ngrok-free.app",
    "https://app.gymos.uz",
    
]


UZ_COUNTRY = "998"
TG_SESSION_TTL = 3600  # 1 hour

WEBAPP_BASE_URL = os.getenv("WEBAPP_BASE_URL", "")

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/api/users/"          # or f"/api/dashboard/app/gyms/1/" for dev
LOGOUT_REDIRECT_URL = "/accounts/login/"


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",

    "users",
    "branches",
    "subscriptions",
    "identifiers",
    "devices",
    "access",
    "dashboard",
    "telegram_bot",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    'django.middleware.locale.LocaleMiddleware',
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # optional
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "dashboard.context_processors.gym_saas_banner"
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DB_NAME", BASE_DIR / "db.sqlite3"),
        "USER": os.getenv("DB_USER", ""),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
    }
}
AUTH_USER_MODEL = "users.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Tashkent")
USE_I18N = True
USE_TZ = True

USE_L10N = True

LANGUAGE_CODE = 'uz'

LANGUAGES = [
    ('uz', 'Uzbek'),
    ('ru', 'Russian'),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]



STATIC_URL = "static_root/"
STATIC_ROOT = os.path.join(BASE_DIR, 'static_root')
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "kiosk_ip": "60/min",       # per IP
        "kiosk_device": "300/min",  # per device
    },
}