from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY")
# SECRET_KEY = "django-insecure-abl=ifw_n4j0o!5zu&wc3&u_vst#$^9$skuvd-pg*phjgg$e9q"
DJANGO_ENV = config("DJANGO_ENV")

# DEBUG = True

# ALLOWED_HOSTS = []

# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000",
# ]

if DJANGO_ENV == "local":

    DEBUG = config("DEBUG", default=True, cast=bool)
    CSRF_COOKIE_SECURE = False
    CSRF_COOKIE_HTTPONLY = False

    # ALLOWED_HOSTS = ['*']
    ALLOWED_HOSTS = [
        "127.0.0.1",  # Локальный хост для тестов
        "localhost",  # Чтобы поддерживать локальный доступ через localhost
    ]
    CORS_ALLOW_ALL_ORIGINS = True

    # MEDIA_ROOT = BASE_DIR / "media"
    # MEDIA_URL = "/media/"

    # FRONT_URL = "http://localhost:3000"
    # DOMAIN = "localhost:8000"

else:

    DEBUG = False
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True

    ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())
    CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="", cast=Csv())

    # MEDIA_ROOT = STATIC_ROOT / "media"
    # MEDIA_URL = "/static/media/"
    # DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

    # FRONT_URL = "https://kid-front.onrender.com"
    # DOMAIN = "kid-wlsf.onrender.com"


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "notes_app",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "workbench_django.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "workbench_django.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
