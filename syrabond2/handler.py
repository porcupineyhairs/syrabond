import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'syrabond2.settings')

from django.apps import apps
from django.conf import settings
apps.populate(settings.INSTALLED_APPS)

from syrabond2.main_app.models import *
from syrabond2.main_app.mqttsender import Mqtt


class MessageHandler:

    MODELS = [
        'Switch',
        'Sensor'
    ]

    def __init__(self):
        self.resources = {}
        self.listener = Mqtt(
            'syrabond_listener_' + str(uuid()), clean_session=True, handler=self
        )
        self.load_resources()

    def load_resources(self):
        for mod in self.MODELS:
            model = globals()[mod]
            qs = model.objects.all()
            for obj in qs:
                self.resources.update({obj.uid: obj})
                obj.connect(self.listener)

    def handle(self, payload):
        _type, _id, channel, msg = payload
        if _type == 'switch':
            switch = self.resources.get(_id)
            print(switch)
            if switch:
                switch.refresh_from_db()
                switch.update_state(msg)
        elif _type == 'sensor':
            try:
                ind = float(msg)
            except ValueError:
                return
            sensor = self.resources.get(_id)
            if sensor:
                sensor.refresh_from_db()
                sensor.update_state(channel=channel, ind=ind)
