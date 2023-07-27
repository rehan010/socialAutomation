from __future__ import absolute_import, unicode_literals
import os
# from django.conf import settings
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Automatation.settings')

app = Celery('app',
                broker='redis://localhost:6379/0',
                backend='redis://localhost:6379/0'
                ) # config is the name of the app having setting files

# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')


# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # Define your periodic tasks (cron-like jobs) here
    'your_periodic_task_name': {
        'task': 'app.tasks.task_one',  # Path to the periodic task
        'schedule': crontab(),  # Example: Run the task every 15 minutes
    },

}