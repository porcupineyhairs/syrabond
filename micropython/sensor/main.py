import machine
import ubinascii
import network
import pauchok
from time import sleep

error_count = 0
max_error = 10

# ---------------------- common section ---------------------------
sta_if = network.WLAN(network.STA_IF)
netconf = 0
while not netconf:
    if sta_if.isconnected():
        netconf = sta_if.ifconfig()
config = pauchok.get_config('conf.json')
mqtt = config['mqtt']
module = config['module']
period = int(config["period"])
interval = int(config["interval"])/period
debug = bool(config['debug'])
uniqid = module['type']+'-'+ubinascii.hexlify(machine.unique_id()).decode()+'-v'+module['ver']
config.clear()
led = int(module['led'])

mqttsender = pauchok.Mqttsender(mqtt, netconf[0], uniqid)
mqttsender.connect()
topic = mqtt['object']+'/'+mqtt['channel']+'/'+uniqid
mqtt.clear()
# ---------------------- end common section -----------------------
# TODO Should make mutitype module codeflow
if not debug:
    n = interval
    while True:
        i = 5
        while i:
            mqttsender.c.check_msg()
            mqttsender.processing()
            i -= 1
        if error_count > 0:
            print('Errors to reboot: ', max_error - error_count)
            if error_count > max_error:
                print('Rebooting...')
                machine.reset()
        if n == interval:
            n = 0
            if led:
                blink = machine.Pin(led, machine.Pin.OUT)
            gc.collect()
            print (module['type'])
            mod = __import__(module['type'])
            if led:
                blink.value(abs(blink.value()-1))
            try:
                inst = mod.MOD(module['type'] + '.json')
                reading = inst.do()
            except:
                reading = 'Error'
            if reading == 'Error':
                    print ('Error!')
                    ERRC += 1
            else:
                for res in reading:
                    #print(topic+'/'+res, reading[res])
                    mqttsender.send(topic+'/'+res, reading[res])
            if led:
                blink.value(abs(blink.value()-1))
        sleep(period)
        n += 1
