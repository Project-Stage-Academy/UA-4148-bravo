import os
from core.settings.base_settings import BASE_DIR

# Logs
LOG_DIR = BASE_DIR / 'logs'
try:
    LOG_DIR.mkdir(exist_ok=True)
except Exception as e:
    print(f"Could not create log dir: {e}")

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
            'delay': True,
        },
        'file_apps': {
            'level': 'DEBUG',
            'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'apps.log'),
            'backupCount': 7,
            'formatter': 'verbose',
            'encoding': 'utf-8',
            'mode': 'a',
            'delay': True,
        },
        'file_errors': {
            'level': 'ERROR',
            'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'errors.log'),
            'backupCount': 7,
            'formatter': 'verbose',
            'encoding': 'utf-8',
            'mode': 'a',
            'delay': True,
        },
        'db_file': {
            'level': 'INFO',
            'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'db_queries.log'),
            'backupCount': 7,
            'formatter': 'verbose',
            'encoding': 'utf-8',
            'mode': 'a',
            'delay': True,
        },
        'file_json': {
            'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'json_logs.log'),
            'backupCount': 7,
            'formatter': 'json',
            'level': 'INFO',
            'encoding': 'utf-8',
            'mode': 'a',
            'delay': True,
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