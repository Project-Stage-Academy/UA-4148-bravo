import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('forum_project')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.broker_url = 'redis://localhost:6379/0'
app.conf.result_backend = 'redis://localhost:6379/0'

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'cleanup-email-tokens-weekly': {
        'task': 'users.tasks.cleanup_email_tokens',
        'schedule': 604800.0,
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
