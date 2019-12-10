from machine import Pin
import machine
from time import sleep
from time import ticks_ms
from time import ticks_diff


class Switch:

    def __init__(self, mqtt, pin, led, button, level, topic):
        self.pin = Pin(pin, Pin.OUT)
        self.led = Pin(led, Pin.OUT)
        if isinstance(button, int):
            self.button = Pin(button, Pin.IN)
            self.button.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.push)
            self.blocking = False
        else:
            self.button = False
        self.change_flag = False
        self.topic = topic
        self.ON = int(level)
        self.OFF = abs(self.ON-1)
        self.mqtt = mqtt
        self.mqtt.subscribe(self.topic, self.callback)
        self.start = 0
    
    def callback(self, topic, msg):
        print('Got '+msg.decode()+' in '+topic.decode())
        if msg == b"on":
            self.pin.value(self.ON)
            self.led.value(0)
        elif msg == b"off":
            self.pin.value(self.OFF)
            self.led.value(1)
        if topic.decode() == self.mqtt.topic_ping:
            if msg.decode() == 'PING':
                self.mqtt.send(self.mqtt.topic_lastwill, self.mqtt.ip)
        if topic.decode() == self.mqtt.topic_management:
            self.mqtt.manage(msg.decode())

    def push(self, button):
        if self.button.value() == 0:
            self.start = ticks_ms()
            self.blocking = True
        elif self.button.value() == 1:
            if self.blocking:
                if ticks_diff(ticks_ms(), self.start) > 5000:
                    machine.reset()
                print('Switching by button')
                sleep(0.5)
                # self.pin.value(abs(self.pin.value() - 1))
                if self.pin.value() == self.ON:
                    self.pin.value(self.OFF)
                    self.led.value(1)
                elif self.pin.value() == self.OFF:
                    self.pin.value(self.ON)
                    self.led.value(0)
                self.change_flag = True
                self.blocking = False
                sleep(0.5)

    def update_site(self):
        if self.change_flag:
            if self.pin.value() == self.ON:
                self.mqtt.send(self.topic, 'on')
            elif self.pin.value() == self.OFF:
                self.mqtt.send(self.topic, 'off')
            self.change_flag = False


