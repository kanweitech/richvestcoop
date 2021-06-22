from __future__ import absolute_import
import os
from django.conf import settings
from celery import Celery
from celery.schedules import crontab

# setting Django SETTINGS as default
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richvestcoop.settings')

app = Celery("richvestcoop")

app.config_from_object('django.conf.settings', namespace='CELERY')

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


app.conf.update(
    CELERYBEAT_SCHEDULE={
        'reserve_nuban': {
            'task': 'acctmang.reserve_nuban_task',
            'schedule': crontab(minute='0')
        },
    }
)

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

