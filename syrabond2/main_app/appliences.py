from uuid import uuid4 as uuid

from syrabond import mqttsender

from .models import Resource, State

class Switch:

    sender = mqttsender.Mqtt('syrabond_sender_' + str(uuid()), config='mqtt.json', clean_session=True)

    # Mapping 'what-to-send': 'what-to-store'
    command_map = {
        'off': 'OFF',
        'on': 'ON'
    }

    def __init__(self, r: Resource):
        self.res = r
        self.uid = self.res.uid
        if not self.res.state:
            self.res.state = State()
            self.res.state.save()

    @property
    def topic(self):
        return self.res.facility.key+'/'+str(self.res.type)+'/'+self.uid

    def on(self):
        try:
            self.sender.mqttsend(self.topic, 'on', retain=True)
            self.res.state.current = Switch.command_map['on']
            self.res.state.save()
            return True
        except Exception as e:
            print(f'Error while turning {self.uid} on: {e}')
            return False

    def off(self):
        try:
            self.sender.mqttsend(self.topic, 'off', retain=True)
            self.res.state.current = Switch.command_map['off']
            self.res.state.save()
            return True
        except Exception as e:
            print(f'Error while turning {self.uid} off: {e}')
            return False

    class Meta:
        abstract = True
