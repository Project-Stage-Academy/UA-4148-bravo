import sys
import uuid
from datetime import timedelta
import mongoengine
from typing import Any
from core.settings.base_settings import DEBUG, SECRET_KEY
from utils.get_env import get_env

AUTHENTICATION_BACKENDS = [
    'users.backends.EmailBackend',
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.github.GithubOAuth2',
    'django.contrib.auth.backends.ModelBackend',
]

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = get_env('GOOGLE_CLIENT_ID')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = get_env('GOOGLE_CLIENT_SECRET')

SOCIAL_AUTH_GITHUB_KEY = get_env('GITHUB_CLIENT_ID')
SOCIAL_AUTH_GITHUB_SECRET = get_env('GITHUB_CLIENT_SECRET')

SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]
SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS = {
    'access_type': 'offline',
    'prompt': 'consent',
}

SOCIAL_AUTH_GITHUB_SCOPE = ['user:email']

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.social_auth.associate_by_email',
    'users.pipelines.create_or_update_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'users.pipelines.activate_verified_user',
    'users.pipelines.safe_user_details',
)

DEFAULT_SCHEMA_CLASS = 'drf_spectacular.openapi.AutoSchema'

REST_FRAMEWORK: dict[str, Any] = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "users.cookie_jwt.CookieJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "users.permissions.IsAuthenticatedOr401",
    ),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": "10/minute",
        "anon": "5/minute",
        "resend_email": "5/minute"
    },
    "DEFAULT_SCHEMA_CLASS": 'drf_spectacular.openapi.AutoSchema'
}

if 'test' in sys.argv:
    REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []

# drf-spectacular settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'Your API',
    'DESCRIPTION': 'REST API for authentication and account management (and more).',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # gated by URLConf/env using DOCS_ENABLED
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'COMPONENT_SPLIT_REQUEST': True,
    'SECURITY': [{'bearerAuth': []}],
    'AUTHENTICATION_WHITELIST': [],
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    'POSTPROCESSING_HOOKS': [],
    'CONTACT': {'name': 'Team', 'email': 'support@example.com'},
    'LICENSE': {'name': 'Proprietary'},
    'SCHEMA_PATH_PREFIX': r'/api/v1',
    'SERVE_URLCONF': None,
    'ENUM_NAME_OVERRIDES': {},
    'SCHEMA_EXTENSIONS': [],
    'SECURITY_SCHEMES': {
        'bearerAuth': {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        }
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=get_env("ACCESS_TOKEN_MINUTES", default=30, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=get_env("REFRESH_TOKEN_DAYS", default=1, cast=int)),
    'BLACKLIST_AFTER_ROTATION': True,
    'ROTATE_REFRESH_TOKENS': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': (
        'rest_framework_simplejwt.tokens.AccessToken',
        'rest_framework_simplejwt.tokens.RefreshToken',
    ),
    'USER_ID_FIELD': 'user_id',
    'USER_ID_CLAIM': 'user_id',
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,

    # Cookie settings
    "AUTH_COOKIE": "access_token",
    "AUTH_COOKIE_DOMAIN": None,
    "AUTH_COOKIE_SECURE": not DEBUG,
    "AUTH_COOKIE_HTTP_ONLY": True,
    "AUTH_COOKIE_PATH": "/",
    "AUTH_COOKIE_SAMESITE": "Lax",
}

# CSRF
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SECURE_SSL_REDIRECT = False

DJOSER = {
    'LOGIN_FIELD': 'email',
    'USER_CREATE_PASSWORD_RETYPE': True,
    # Pass recovery
    'CUSTOM_PASSWORD_RESET_CONFIRM_URL': 'users/reset_password_confirm/{uid}/{token}',  # link for front-end developer
    'PASSWORD_RESET_TIMEOUT': 3600,
    'PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND': True,

    'SEND_ACTIVATION_EMAIL': True,
    'SEND_CONFIRMATION_EMAIL': True,
    'PASSWORD_CHANGED_EMAIL_CONFIRMATION': True,
    'USERNAME_CHANGED_EMAIL_CONFIRMATION': True,
    'PASSWORD_RESET_CONFIRM_URL': 'password/reset/confirm/{uid}/{token}',
    'USERNAME_RESET_CONFIRM_URL': 'email/reset/confirm/{uid}/{token}',
    'ACTIVATION_URL': 'activate/{uid}/{token}',
    'SERIALIZERS': {
        'user_create': 'users.serializers.CustomUserCreateSerializer',
        'user': 'users.serializers.CustomUserSerializer',
        'current_user': 'users.serializers.CustomUserSerializer',
        'activation': 'djoser.serializers.ActivationSerializer',
    },
    'EMAIL': {
        'activation': 'djoser.email.ActivationEmail',
        'confirmation': 'djoser.email.ConfirmationEmail',
    },
    'USER_ID_FIELD': 'user_id',
}

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Email Configuration (for development)
    DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = get_env('EMAIL_HOST')
    EMAIL_PORT = get_env("EMAIL_PORT", default=587, cast=int)
    EMAIL_HOST_USER = get_env('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = get_env('EMAIL_HOST_PASSWORD')
    EMAIL_USE_TLS = get_env("EMAIL_USE_TLS", default=True, cast=bool)
    DEFAULT_FROM_EMAIL = get_env('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': get_env('DB_NAME', required=True),
        'USER': get_env('DB_USER', required=True),
        'PASSWORD': get_env('DB_PASSWORD', required=True),
        'HOST': get_env('DB_HOST', default='localhost'),
        'PORT': get_env('DB_PORT', default='5432'),
        'TEST': {
            'NAME': f'test_db_{uuid.uuid4().hex[:8]}',
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'users.validators.CustomPasswordValidator',
    },
]

# CORS configuration for local development
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# CSRF configuration for local development
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

CORS_ALLOW_CREDENTIALS = True

# Elasticsearch DSL Configuration
ELASTICSEARCH_HOST = get_env('ELASTICSEARCH_HOST', default='http://localhost:9200')
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': ELASTICSEARCH_HOST,
    },
}

# Override Elasticsearch index names for testing
if 'users' in sys.argv:
    ELASTICSEARCH_DSL = {
        'default': {'hosts': ELASTICSEARCH_HOST}
    }

# Celery
REDIS_URL = get_env("REDIS_URL", default="redis://127.0.0.1:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

if 'test' in sys.argv:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True

# Chat
ASGI_APPLICATION = "core.asgi.application"
REDIS_HOST = get_env("REDIS_HOST", "127.0.0.1")
REDIS_PORT = get_env("REDIS_PORT", default=6379, cast=int)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
        },
    },
}

MONGO_DB = get_env("MONGO_DB", "chat_test")
MONGO_HOST = get_env("MONGO_HOST", "127.0.0.1")
MONGO_PORT = get_env("MONGO_PORT", default=27017, cast=int)
MONGO_USER = get_env("MONGO_INITDB_ROOT_USERNAME", "root")
MONGO_PASSWORD = get_env("MONGO_INITDB_ROOT_PASSWORD", "secret")

if MONGO_USER and MONGO_PASSWORD:
    uri = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin"
else:
    uri = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}"

mongoengine.connect(db=MONGO_DB, host=uri, alias="chat", serverSelectionTimeoutMS=5000)
