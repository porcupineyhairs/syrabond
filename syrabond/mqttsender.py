import paho.mqtt.client as mqtt
import sys
from time import sleep
from syrabond.common import extract_config
from syrabond.common import log


class Mqtt:
    """
    Wrapper class for paho.mqtt.client.
    Handles connecting, subscribing, receiving and sending MQTT-messages.
    Holds the messages in own message buffer that used by other classes to get messages.
    Accepts mqtt.json file in config dir to get config.
    """

    def __init__(self, name, config='mqtt.json', clean_session=True):
        self.connected = False
        mqtt_config = extract_config(config)
        self.name = name
        self.clean_session = clean_session
        self.root = mqtt_config['object_name']
        self.broker = mqtt_config['server']
        self.ping_topic = mqtt_config['ping_topic']
        self.client = mqtt.Client(self.name, clean_session=self.clean_session)
        self.client.username_pw_set(username=mqtt_config['user'], password=mqtt_config['password'])
        self.client.on_message = self.message_to_buffer
        self.client.on_disconnect = self.on_disconnect
        self.message_buffer = {}
        self.message_buffer_lock = False

    def connect(self):
        try:
            print('Connecting...')
            #log('Connecting...')
            if not self.client.connect(self.broker):
                self.connected = True
        except Exception as e:
            log('Connection error: {}'.format(e), log_type='error')
            return False
        log('Connected to broker on {} as {}'.format(self.broker, self.name))
        return True

    def mqttsend(self, topic: str, msg: str, retain=False):
        """Sends msg to topic. Logs activity and errors."""
        if not self.connected:
            self.connect()
        log('Sending {} to {}...'.format(msg, topic))
        try:
            self.client.publish(topic, msg, retain=retain)
        except Exception as e:
            log('Error while sending: {}.'.format(e), log_type='error')
            return False
        print('Message sent.')
        log('Message sent.', log_type='debug')
        if self.clean_session:
            self.client.disconnect()
            self.connected = False
            print('Disconnected')
        return True

    def subscribe(self, topic):
        """Subscribes to the topic specifies. Logs activity and errors."""
        while not self.connected:
            if not self.connect():
                sleep(5)
        try:
            self.client.subscribe(topic)
            log('Subscribed: '+topic, log_type='debug')
            return True
        except Exception as e:
            log('Could not subscribe', log_type='error')
            return False

    def check_for_messages(self):
        if not self.message_buffer_lock:
            self.client.loop()

    def wait_for_messages(self):
        self.client.loop_forever()

    def message_to_buffer(self, client, userdata, message):
        if message:
            log(' Got {} in {}'.format(message.payload.decode(), message.topic), log_type='debug')
            self.message_buffer.update({message.topic: message.payload.decode()})

    def disconnect(self):
        self.client.disconnect()
        self.connected = False
        print('Disconnected')

    def on_disconnect(self, client, userdata, rc=0):
        log("Disconnected result code " + str(rc), log_type='debug')
        client.loop_stop()


class Dumb:

    def __init__(self):
        pass

    def connect(self):
        pass
        #print('Dumb would not connect')

    def subscribe(self, topic):
        pass
        #print('Dumb would not subscribe')


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Wrong arguments")
        print("Usage: mqttsender.py <topic> <message>")
        sys.exit(-1)
    topic = sys.argv[1]
    msg = sys.argv[2]
    sender = Mqtt('Python_mqtt_sender')
    sender.mqttsend(topic, msg)
