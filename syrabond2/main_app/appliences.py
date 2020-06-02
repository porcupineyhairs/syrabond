from uuid import uuid4 as uuid

from .mqttsender import Mqtt

class Comm:

    #'to send': 'to store'
    command_map = {
        'off': 'OFF',
        'on': 'ON'
    }

    mqtt = Mqtt('syrabond_sender_' + str(uuid()), clean_session=True)


class ResourceApp:

    def connect(self, listener):
        listener.subscribe(self.topic)


class SwitchApp:

    def __init__(self, *args, **kwargs):
        self.sender = Comm.mqtt

    def update_state(self, state):
        switch = self
        if switch.state.current != Comm.command_map.get(state) and Comm.command_map.get(state):
            switch.state.current = Comm.command_map[state]
            switch.state.save()

    def on(self):
        try:
            self.sender.mqttsend(self.topic, 'on', retain=True)
            self.state.current = Comm.command_map['on']
            self.state.save()
            return True
        except Exception as e:
            print(f'Error while turning {self.uid} on: {e}')
            return False

    def off(self):
        try:
            self.sender.mqttsend(self.topic, 'off', retain=True)
            self.state.current = Comm.command_map['off']
            self.state.save()
            return True
        except Exception as e:
            print(f'Error while turning {self.uid} off: {e}')
            return False

    def toggle(self):
        try:
            if self.state.current == Comm.command_map['off']:
                self.sender.mqttsend(self.topic, 'on', retain=True)
                self.state.current = Comm.command_map['on']
                self.state.save()
            elif self.state.current == Comm.command_map['on']:
                self.sender.mqttsend(self.topic, 'off', retain=True)
                self.state.current = Comm.command_map['off']
                self.state.save()
            return True
        except Exception as e:
            print(f'Error while turning {self.uid} off: {e}')
            return False


class SensorApp:

    def update_state(self, channel=None, ind=None):
        sensor = self
        if sensor.state.data:
            if sensor.state.data.get(channel) != ind:
                sensor.state.data[channel] = ind
                sensor.state.save()
        else:
            sensor.state.data = {channel: ind}
