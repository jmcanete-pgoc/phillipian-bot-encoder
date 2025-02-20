import os
from celery import Celery
from celery.schedules import crontab
# Ensure timezone awareness
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'philippian_encoder.settings')
app = Celery("philippian_encoder")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'run-every-day-at-midnight': {
        'task': 'pancake.tasks.monitor_task_tagger',
        'schedule': crontab(minute='*/1'),
        
    },
}

# Ensure timezone awareness
app.conf.timezone = settings.TIME_ZONE



