

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

import sys

from rq import Connection, Worker

from django.apps import apps
from django.conf import settings

from settings import RQ_NAME


#  Activate Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
apps.populate(settings.INSTALLED_APPS)

# Pre-import models to improve performance
from main_app.models import Switch, Sensor

with Connection():
    qs = sys.argv[1:] or [RQ_NAME]

    w = Worker(qs)
    w.work()
