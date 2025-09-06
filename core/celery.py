import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('forum_project')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'cleanup-email-tokens-weekly': {
        'task': 'users.tasks.cleanup_email_tokens',
        'schedule': 604800.0,
    },
    'check-unbound-inactive-users-every-day': {
        'task': 'users.tasks.check_unbound_inactive_users',
        'schedule': crontab(hour=0, minute=0),
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
