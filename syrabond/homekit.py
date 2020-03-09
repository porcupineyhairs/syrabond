from threading import Thread

from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_SWITCH, CATEGORY_SENSOR, CATEGORY_THERMOSTAT

from .common import log


class iSensor(Accessory):

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

    @Accessory.run_at_interval(30)
    def run(self):
        if self.temp and self.resource.state.get('temp'):
            self.char_temp.set_value(float(self.resource.state['temp']))
        if self.hum and self.resource.state.get('hum'):
            self.char_temp.set_value(float(self.resource.state['hum']))


class iSwitch(Accessory):

    category = CATEGORY_SWITCH

    state_map = {
        'OFF': 0,
        'ON': 1
    }

    def __init__(self, *args, **kwargs):

        api_settings = kwargs.pop('api_settings')

        super().__init__(*args, **kwargs)

        serv_switch = self.add_preload_service('Switch')
        self.switch = serv_switch.configure_char('On', setter_callback=self.toggle)
        self.resource = api_settings['resource']

    def toggle(self, value):
        self.resource.off() if value == self.state_map.get(self.resource.command_map['off']) else self.resource.on()


    @Accessory.run_at_interval(3)
    def run(self):
        if self.switch.value != self.state_map.get(self.resource.state):
            self.switch.notify()


class HomeKit:

    def __init__(self, facility):
        self.driver, self.driver_thread = None, None
        self.facility = facility
        self.make_bridge()

    def make_bridge(self):
        self.driver = AccessoryDriver(port=51826, persist_file='sh.state')
        self.driver.add_accessory(accessory=get_bridge(self.driver, self.facility))

    def run(self):
        log(f'Running HomeKit bridge. Pin: {self.driver.state.pincode.decode()}')
        self.driver_thread = Thread(target=self.driver.start)
        self.driver_thread.start()

    def stop(self):
        self.driver.stop()
        self.driver_thread.join()


def get_bridge(driver, facility):
    bridge = Bridge(driver, 'Syrabond Bridge')
    for resource in facility.resources.values():
        bridge.add_accessory(
            iSwitch(driver, resource.hrn, api_settings={'resource': resource})
        ) if resource.type == 'switch' else None
        bridge.add_accessory(
            iSensor(driver, resource.hrn, api_settings={'resource': resource})
        ) if resource.type == 'sensor' else None
    return bridge
