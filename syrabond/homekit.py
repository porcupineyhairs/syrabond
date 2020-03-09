import signal
from threading import Thread

from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_SWITCH, CATEGORY_SENSOR

from .common import log


class Sensor(Accessory):

    category = CATEGORY_SENSOR

    def __init__(self, *args, **kwargs):

        api_settings = kwargs.pop('api_settings')

        super().__init__(*args, **kwargs)
        self.resource = api_settings['resource']

        if 'temp' in self.resource.channels:
            self.temp = True
        else:
            self.temp = False
        if 'hum' in self.resource.channels:
            self.hum = True
        else:
            self.hum = False

        if self.temp:
            serv_temp = self.add_preload_service('TemperatureSensor')
            self.char_temp = serv_temp.configure_char('CurrentTemperature')
        if self.hum:
            serv_humidity = self.add_preload_service('HumiditySensor')
            self.char_humidity = serv_humidity.configure_char('CurrentRelativeHumidity')
        print(self.resource)

    @Accessory.run_at_interval(10)
    def run(self):
        if self.temp:
            self.char_temp.set_value(float(self.resource.state.get('temp')))
        if self.hum:
            self.char_humidity.set_value(float(self.resource.state.get('hum')))


class Switch(Accessory):

    category = CATEGORY_SWITCH

    def __init__(self, *args, **kwargs):

        api_settings = kwargs.pop('api_settings')

        super().__init__(*args, **kwargs)

        serv_switch = self.add_preload_service('Switch')
        self.char_on = serv_switch.configure_char('On', setter_callback=self.toggle)
        self.resource = api_settings['resource']
        print(self.resource)

    def toggle(self, value):
        self.resource.off() if value == 0 else self.resource.on()


class HomeKit:

    def __init__(self, facility):
        self.driver = None
        self.facility = facility
        self.make_bridge()

    def make_bridge(self):
        self.driver = AccessoryDriver(port=51826, persist_file='sh.state')
        self.driver.add_accessory(accessory=get_bridge(self.driver, self.facility))
        signal.signal(signal.SIGTERM, self.driver.signal_handler)

    def run(self):
        log(f'Running HomeKit bridge. Pin: {self.driver.state.pincode.decode()}')
        Thread(target=self.driver.start).start()


def get_bridge(driver, facility):
    bridge = Bridge(driver, 'Syrabond Bridge')
    for resource in facility.resources.values():
        bridge.add_accessory(
            Switch(driver, resource.hrn, api_settings={'resource': resource})
        ) if resource.type == 'switch' else None
        bridge.add_accessory(
            Sensor(driver, resource.hrn, api_settings={'resource': resource})
        ) if resource.type == 'sensor' else None
    return bridge
