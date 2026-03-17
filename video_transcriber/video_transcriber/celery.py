import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'video_transcriber.settings')
app = Celery('video_transcriber')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()