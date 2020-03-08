import signal

from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_SWITCH


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


def get_bridge(driver, facility):
    """Call this method to get a Bridge instead of a standalone accessory."""
    bridge = Bridge(driver, 'Syrabond Bridge')
    for resource in facility.resources.values():
        bridge.add_accessory(Switch(driver, resource.hrn, api_settings={'resource': resource})) if resource.type == 'switch' else None
    return bridge


def run_bridge(facility):
    print('RUN HOMEKIT')
    driver = AccessoryDriver(port=51826, persist_file='sh.state')
    driver.add_accessory(accessory=get_bridge(driver, facility))
    #signal.signal(signal.SIGTERM, driver.signal_handler)
    driver.start()
