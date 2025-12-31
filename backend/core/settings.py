import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# Core Config
# =============================================================================
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-this-for-prod")
DEBUG = os.getenv("DEBUG", "True") == "True"
ENV = os.getenv("ENV", "development")  # Optionally set ENV=production in prod

# Production domains, set via env in prod
ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0,backend"
).split(",")

# =============================================================================
# Installed Apps
# =============================================================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "rest_framework",
    "rest_framework_gis",
    "corsheaders",
    "django_filters",
    "drf_yasg",
    "api",
    "observations",
    "users",
    "species",
]

# =============================================================================
# Middleware
# =============================================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

# Password reset settings
PASSWORD_RESET_TIMEOUT = 259200  # 3 days in seconds

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

WSGI_APPLICATION = "core.wsgi.application"

# =============================================================================
# Database
# =============================================================================
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.getenv("DB_NAME", "marine_tracker"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
        "HOST": os.getenv("DB_HOST", "db"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        )
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {
        "NAME": (
            "django.contrib.auth.password_validation.CommonPasswordValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.NumericPasswordValidator"
        )
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# Static/Media
# =============================================================================
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# =============================================================================
# Django REST Framework
# =============================================================================
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": (
        "rest_framework.pagination.PageNumberPagination"
    ),
    "PAGE_SIZE": 25,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend"
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "users.authentication.CookieJWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
}
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),  # Recommended: 15 minutes
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),  # Recommended: 7 days
    "ROTATE_REFRESH_TOKENS": True,  # Recommended: Enabled
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_COOKIE": (
        "access_token"
    ),  # The name of the cookie for the access token
    "AUTH_COOKIE_REFRESH": (
        "refresh_token"
    ),  # The name of the cookie for the refresh token
    "AUTH_COOKIE_DOMAIN": None,
    "AUTH_COOKIE_SECURE": True,  # Recommended: Secure
    "AUTH_COOKIE_HTTP_ONLY": True,  # Recommended: HttpOnly
    "AUTH_COOKIE_SAMESITE": "Lax",  # Recommended: SameSite=Lax
    "AUTH_COOKIE_PATH": "/",
    "AUTH_COOKIE_EXPIRE_DAYS": 7,  # Expiration of the refresh cookie
}
# =============================================================================
# CORS
# =============================================================================
CORS_ALLOW_CREDENTIALS = True

# Default dev origins (use env for prod!)
CORS_ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://0.0.0.0",
).split(",")

# Add trusted origins for CSRF
CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
).split(",")
# =============================================================================
# Security Settings — AUTO-SWITCH for DEV vs PROD
# =============================================================================
if DEBUG or ENV == "development":
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = "Lax"
    # Optional: For DRF Swagger etc. in dev, you may want all hosts
    ALLOWED_HOSTS = ["*"]
    SECURE_HSTS_SECONDS = 0
    # CORS/URLs already set for dev above
else:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Lax"
    X_FRAME_OPTIONS = "DENY"
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = False
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    # CORS: restrict to your real frontend(s) only
    CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    # ALLOWED_HOSTS: restrict to prod domains
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")
    SESSION_COOKIE_DOMAIN = ".kuroshio-lab.com"
    CSRF_COOKIE_DOMAIN = ".kuroshio-lab.com"
    SIMPLE_JWT["AUTH_COOKIE_DOMAIN"] = ".kuroshio-lab.com"

# =============================================================================
# AWS S3 (for prod)
# =============================================================================
USE_S3 = os.getenv("USE_S3", "False") == "True"
if USE_S3:
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "us-east-1")
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

# =============================================================================
# RE-SEND Configuration
# =============================================================================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.resend.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "resend"
EMAIL_HOST_PASSWORD = os.getenv("RESEND_API")

# The default 'From' address for all emails sent by Django (e.g., password resets)
DEFAULT_FROM_EMAIL = "Kuroshio Lab <no-reply@notifications.kuroshio-lab.com>"

# The address for error messages sent to ADMINS (optional, can be same as above)
SERVER_EMAIL = DEFAULT_FROM_EMAIL
# =============================================================================
# Silence drf_yasg format deprecation warning:
# =============================================================================
SWAGGER_USE_COMPAT_RENDERERS = False

# =============================================================================
# Optional: Sentry or other error reporting in prod
# =============================================================================
# if not DEBUG:
#     import sentry_sdk
#     sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'), environment=ENV)

# Custom settings for OBIS/WoRMS clients (used in species.tasks.obis_etl)
OBIS_API_BASE_URL = os.environ.get(
    "OBIS_API_BASE_URL", "https://api.obis.org/v3/"
)
OBIS_API_DEFAULT_SIZE = int(os.environ.get("OBIS_API_DEFAULT_SIZE", 500))
OBIS_DEFAULT_GEOMETRY = os.environ.get(
    "OBIS_DEFAULT_GEOMETRY",
    "POLYGON((-180 -90, 180 -90, 180 90, -180 90, -180 -90))",
)
OBIS_DEFAULT_FETCH_PAGES = int(os.environ.get("OBIS_DEFAULT_FETCH_PAGES", 1))

WORMS_API_BASE_URL = os.environ.get(
    "WORMS_API_BASE_URL", "https://www.marinespecies.org/rest/"
)

# =============================================================================
# Logging Configuration
# =============================================================================
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO" if not DEBUG else "DEBUG")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": (
                "{levelname} {asctime} {module} {process:d} {thread:d}"
                " [User:{user}] {message}"
            ),
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "filters": {
        "user_filter": {
            "()": "core.logging_utils.UserFilter",
        },
    },
    "handlers": {
        "console": {
            "level": LOGGING_LEVEL,
            "filters": ["user_filter"],
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOGGING_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "users": {
            "handlers": ["console"],
            "level": LOGGING_LEVEL,
            "propagate": False,
        },
    },
}
