import machine
import ujson as json
import gc
from uos import urandom as rnd
import network
from time import sleep

def get_config():
    try:
     with open("/network.json") as f:
       data = json.loads(f.read())
       return (data)
    except (OSError, ValueError):
        print("Couldn't load /network.json")
        ap_if = network.WLAN(network.AP_IF)
        ap_if.active(True)
        print(ap_if.ifconfig())
        import webrepl
        webrepl.start()
        import webcreds
        serv = webcreds.Http()
        conn_flag = 0
        if serv:
            while True:
                serv.get_request()
                if serv.raw_requestline:
                    conn_flag = 1
                    serv.parse_request()
                    serv.handle_request()
                if conn_flag:
                    led.value(0)
                    sleep(0.5)
                else:
                    led.value(0)
                    sleep(1.5)
                    led.value(1)
                    sleep(0.5)



def do_connect(config):
    if led:
        led.value(0)
    t = int.from_bytes(rnd(1), 'little') // 12 + 1
    print('Waiting ' + str(t) + ' sec.')  # wait randomized time to balance the load
    sleep(t)
    sta_if = network.WLAN(network.STA_IF)
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)
    if not sta_if.isconnected():
        print('Connecting to network...')
        sta_if.active(True)
        sta_if.connect(config['ssid'], config['pass'])
        t = 0
        serv = None
        conn_flag = 0
        while not sta_if.isconnected():
            if t < 60:
                if led:
                    led.value(0)
                sleep(0.5)
                if led:
                    led.value(1)
                sleep(0.5)
                t += 1
                pass
            else:
                if not ap_if.active():
                    print('Could not connect to network. Setting up soft AP and keep trying...')
                    ap_if.active(True)
                    print(ap_if.ifconfig())
                    import webrepl
                    webrepl.start()
                    import webcreds
                    serv = webcreds.Http()
                if serv:
                    serv.get_request()
                    if serv.raw_requestline:
                        conn_flag = 1
                        serv.parse_request()
                        serv.handle_request()
                    if serv.mainloop_disactive:
                        while True:
                            serv.get_request()
                            if serv.raw_requestline:
                                serv.parse_request()
                                serv.handle_request()
                            sleep(1)
                if conn_flag:
                    if led:
                        led.value(0)
                    sleep(1)
                    if led:
                        led.value(1)
                else:
                    if led:
                        led.value(0)
                    sleep(1.5)
                    if led:
                        led.value(1)
                    sleep(0.5)
    print('Connected:', sta_if.ifconfig())
    ap_if.active(False)
    if led:
        led.value(1)


led = None
config = get_config()
if 'led' in config:
    led = machine.Pin(int(config['led']), machine.Pin.OUT)
do_connect(config)
if config['debug']:
    import webrepl
    webrepl.start()
gc.collect()
if led:
    led.value(1)
