import machine
import ubinascii
import network
import pauchok
from time import sleep


# ---------------------- common section ---------------------------
sta_if = network.WLAN(network.STA_IF)
netconf = 0
while not netconf:
    if sta_if.isconnected():
        netconf = sta_if.ifconfig()
ip = netconf[0]
config = pauchok.get_config('conf.json')
mqtt = config['mqtt']
module = config['module']
period = int(config["period"])
interval = int(config["interval"])/period
debug = config['debug']
inited = config['inited']
uniqid = module['type']+'-'+ubinascii.hexlify(machine.unique_id()).decode()+'-v'+module['ver']
config.clear()
led = module['led']

mqttsender = pauchok.Mqttsender(mqtt, ip, uniqid)
mqttsender.connect()

init_topic = 'common/welcome/'
if not inited:
    mqttsender.send(init_topic+uniqid, ip)
else:
    mqttsender.send(mqttsender.topic_lastwill, ip)
topic = mqtt['object']+'/'+mqtt['channel']+'/'+uniqid
mqtt.clear()
# ---------------------- end common section -----------------------

# TODO Should make mutitype module codeflow
if not debug:
    n = interval
    error_counter = 0
    max_error = 10
    while True:
        i = 5
        while i:
            mqttsender.c.check_msg()
            mqttsender.processing()
            i -= 1
        if error_counter > 0:
            print('Errors to reboot: ', max_error - error_counter)
            if error_counter > max_error:
                print('Rebooting...')
                machine.reset()
        if n == interval:
            n = 0
            if led:
                blink = machine.Pin(led, machine.Pin.OUT)
            gc.collect()
            print(module['type'])
            mod = __import__(module['type'])
            if led:
                blink.value(abs(blink.value()-1))
            try:
                inst = mod.MOD(module)
                reading = inst.do()
            except:
                reading = 'Error'
            if reading == 'Error':
                    print('Error!')
                    error_counter += 1
            else:
                for channel in reading:
                    mqttsender.send(topic+'/'+channel, reading[channel])
            if led:
                blink.value(abs(blink.value()-1))
        sleep(period)
        n += 1
