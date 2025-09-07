import os
from pathlib import Path
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from utils.get_env import get_env
from decouple import config
from dotenv import load_dotenv 

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security
SECRET_KEY = get_env("SECRET_KEY", required=True, use_decouple=True)
DEBUG = get_env("DEBUG", default=False, cast=bool, use_decouple=True)
DOCS_ENABLED = get_env("DOCS_ENABLED", default=True, cast=bool)

ALLOWED_HOSTS = get_env(
    "ALLOWED_HOSTS",
    default=["127.0.0.1", "localhost", "0.0.0.0"],
    cast=list
)

# Applications
FRONTEND_URL = get_env('FRONTEND_URL', default='http://localhost:3000')

FRONTEND_ROUTES = {
    "verify_email": "/auth/verify-email/{user_id}/{token}/",
    "reset_password": "/password/reset/confirm/{uid}/{token}/",
}

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
    'djoser',
    'django_filters',
    'corsheaders',
    'common',
    'search',

    # API schema / docs
    'drf_spectacular',
    'drf_spectacular_sidecar',

    # Elasticsearch
    'django_elasticsearch_dsl',

    # OAuth
    'social_django',
]

SITE_ID = 1
AUTH_USER_MODEL = 'users.User'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
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

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = get_env('LANGUAGE_CODE', default='en-us')
TIME_ZONE = get_env('TIME_ZONE', default='UTC')
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Tests
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Sentry for monitoring
SENTRY_DSN = get_env("SENTRY_DSN", default=None)

sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.5,
    send_default_pii=True
)
