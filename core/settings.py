import os
import sys
from decouple import config
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='127.0.0.1, localhost, 0.0.0.0',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# Application definition

FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

INSTALLED_APPS = [
    'daphne',
    'channels',
    'chat',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'users',
    'investors',
    'projects',
    'startups',
    'communications',
    'dashboard',
    'investments',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'rest_framework.authtoken',
    'djoser',
    'django_filters',
    'corsheaders',
    "notifications.apps.NotificationsConfig",

    # Elasticsearch
    'django_elasticsearch_dsl',

    # OAuth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
]

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'users.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': config('GOOGLE_CLIENT_ID'),
            'secret': config('GOOGLE_CLIENT_SECRET'),
            'key': '',
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {
            'access_type': 'offline',
            'prompt': 'consent', 
        },
        'FETCH_USERINFO': True,
    },

    'github': {
        'APP': {
            'client_id': config('GITHUB_CLIENT_ID'),
            'secret': config('GITHUB_CLIENT_SECRET'),
            'key': '',
        },
        'SCOPE': ['user:email'],
    }
}

# Ensure email is saved and verified
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'mandatory'
SOCIALACCOUNT_AUTO_SIGNUP = True

AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '5/minute',
        'anon': '2/minute',
        'resend_email': '5/minute',
        
    },
}

if 'test' in sys.argv:
    REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'BLACKLIST_AFTER_ROTATION': True,
    'ROTATE_REFRESH_TOKENS': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': (
        'rest_framework_simplejwt.tokens.AccessToken',
        'rest_framework_simplejwt.tokens.RefreshToken',
    ),
    'USER_ID_FIELD': 'user_id',
    'USER_ID_CLAIM': 'user_id',
}

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
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' # Email Configuration (for development)
    DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.sendgrid.net'
    EMAIL_PORT = 587
    EMAIL_HOST_USER = 'apikey'
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
    EMAIL_USE_TLS = True
    DEFAULT_FROM_EMAIL = 'pbeinner@gmail.com'
    
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' # Email Configuration (for development)
    DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = config('EMAIL_HOST')
    EMAIL_PORT = 587
    EMAIL_HOST_USER = config('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
    EMAIL_USE_TLS = True
    DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)

MIDDLEWARE = [
    "allauth.account.middleware.AccountMiddleware",  # OAuth
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

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

WSGI_APPLICATION = 'core.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# if DEBUG:
#    AUTH_PASSWORD_VALIDATORS = []
# else:
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

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = config('LANGUAGE_CODE', default='en-us')
TIME_ZONE = config('TIME_ZONE', default='UTC')
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOW_ALL_ORIGINS = True

# Elasticsearch DSL Configuration
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': config('ELASTICSEARCH_HOST', default='http://localhost:9200'),
    },
}

# Override Elasticsearch index names for testing
if 'users' in sys.argv:
    ELASTICSEARCH_DSL['default']['hosts'] = config('ELASTICSEARCH_HOST', default='http://localhost:9200')

# File validation settings
ALLOWED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png"]
ALLOWED_IMAGE_MIME_TYPES = ["image/jpeg", "image/png"]
ALLOWED_IMAGE_MODES = ["RGB", "RGBA", "L"]
MAX_IMAGE_SIZE_MB = 10
MAX_DOCUMENT_SIZE_MB = 20
MAX_IMAGE_DIMENSIONS = (5000, 5000)

ALLOWED_DOCUMENT_EXTENSIONS = [
    "pdf", "doc", "docx", "txt", "odt", "rtf",
    "xls", "xlsx", "ppt", "pptx", "zip", "rar"
]

ALLOWED_DOCUMENT_MIME_TYPES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "application/vnd.oasis.opendocument.text",
    "application/rtf",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/zip",
    "application/x-rar-compressed",
]

# Social platform validation settings
ALLOWED_SOCIAL_PLATFORMS = {
    'facebook': ['facebook.com'],
    'twitter': ['twitter.com'],
    'linkedin': ['linkedin.com'],
    'instagram': ['instagram.com'],
    'youtube': ['youtube.com', 'youtu.be'],
    'tiktok': ['tiktok.com'],
    'telegram': ['t.me', 'telegram.me'],
}

# Communications app: notification types seeding configuration
COMMUNICATIONS_NOTIFICATION_TYPES = [
    {
        'code': 'startup_saved',
        'name': 'Startup Saved',
        'description': 'Notification when a user saves a startup to their favorites',
        'default_frequency': 'immediate',
        'is_active': True,
    },
    {
        'code': 'project_followed',
        'name': 'Project Followed',
        'description': 'Notification when a user follows a project',
        'default_frequency': 'immediate',
        'is_active': True,
    },
    {
        'code': 'message_received',
        'name': 'Message Received',
        'description': 'Notification when a user receives a new message',
        'default_frequency': 'immediate',
        'is_active': True,
    },
    {
        'code': 'project_updated',
        'name': 'Project Updated',
        'description': 'Notification when a followed project is updated',
        'default_frequency': 'daily_digest',
        'is_active': True,
    },
]

# Logs
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.json.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
        'verbose': {
            'format': '{asctime} {levelname} {name} - {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'INFO',
        },
        'file_django': {
            'level': 'INFO',
            'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'django.log'),
            'backupCount': 7,
            'formatter': 'verbose',
            'encoding': 'utf-8',
            'mode': 'a',
        },
        'file_apps': {
            'level': 'DEBUG',
            'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'apps.log'),
            'backupCount': 7,
            'formatter': 'verbose',
            'encoding': 'utf-8',
            'mode': 'a',
        },
        'file_errors': {
            'level': 'ERROR',
            'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'errors.log'),
            'backupCount': 7,
            'formatter': 'verbose',
            'encoding': 'utf-8',
            'mode': 'a',
        },
        'db_file': {
            'level': 'INFO',
            'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'db_queries.log'),
            'backupCount': 7,
            'formatter': 'verbose',
            'encoding': 'utf-8',
            'mode': 'a',
        },
        'file_json': {
            'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'json_logs.log'),
            'backupCount': 7,
            'formatter': 'json',
            'level': 'INFO',
            'encoding': 'utf-8',
            'mode': 'a',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_django', 'file_errors'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console', 'db_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'file_django'],
            'level': 'WARNING',
            'propagate': False,
        },
        'users': {
            'handlers': ['console', 'file_apps'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'startups': {
            'handlers': ['console', 'file_apps'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'investors': {
            'handlers': ['console', 'file_apps'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'projects': {
            'handlers': ['console', 'file_apps'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'communications': {
            'handlers': ['console', 'file_apps'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'dashboard': {
            'handlers': ['console', 'file_apps'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file_errors', 'file_json'],
        'level': 'INFO',
    },
}

# Celery
CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_RESULT_BACKEND = 'rpc://'

if 'users' in sys.argv:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True

# Chat
ASGI_APPLICATION = "core.asgi.application"
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
        },
    },
}

TEST_RUNNER = 'django.test.runner.DiscoverRunner'
