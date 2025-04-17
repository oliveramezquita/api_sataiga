from __future__ import absolute_import
import os
from celery import Celery

# Establece el settings de Django por defecto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_sataiga.settings')

app = Celery('api_sataiga')

# Lee configuración de Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscovery de tareas en apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
