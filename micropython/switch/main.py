import machine
import ubinascii
import network
import pauchok
import switch

# ---------------------- common section ---------------------------
init_topic = 'common/welcome/'
sta_if = network.WLAN(network.STA_IF)
netconf = None
while not netconf:
    if sta_if.isconnected():
        netconf = sta_if.ifconfig()
config = pauchok.get_config('conf.json')
mqtt = config['mqtt']
module = config['module']
sleep_time = int(config["sleep_time"])
debug = bool(config['debug'])
inited = bool(config['inited'])
ip = netconf[0]
uniqid = module['type']+'-'+ubinascii.hexlify(machine.unique_id()).decode()+'-v'+module['ver']
config.clear()
mqttsender = pauchok.Mqttsender(mqtt, ip, uniqid)
mqttsender.connect()

if not inited:
    mqttsender.send(init_topic+uniqid, ip)
else:
    mqttsender.send(mqttsender.topic_lastwill, ip)

topic = mqtt['object']+'/'+mqtt['channel']+'/'+uniqid
mqtt.clear()
# ---------------------- end common section -----------------------
is_error = False
if 'button' in module:
    button = int(module['button'])
else:
    button = False

sw = switch.Switch(mqttsender, int(module['pin']), int(module['led']), button, int(module['level']), topic)
module.clear()

if not debug:
    try:
        while True:
            sw.update_site()
            print('Waiting for message in topic %s...' % sw.topic)
            mqttsender.c.wait_msg()
    except:
        if is_error:
            mqttsender.c.disconnect()
            machine.reset()
        is_error = True
    finally:
        mqttsender.c.disconnect()
        machine.reset()
