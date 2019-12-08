from syrabond import mqttsender, common, database
from uuid import uuid1
from sys import exit


class Facility:

    def __init__(self, name, listen=True):
        self.premises = {}
        self.resources = {}
        self.virtual_apls = {}
        self.tags = {}
        self.name = name
        self.DB = database.Mysql()  # TODO Choose DB interface with config
        uniqid = str(uuid1())
        common.log('Creating Syrabond instance with uuid ' + uniqid)
        if listen:
            self.listener = mqttsender.Mqtt('syrabond_listener_' + uniqid, config='mqtt.json', clean_session=True)
            self.listener.subscribe('{}/{}/#'.format(self.name, 'status'))  # TODO Dehardcode status topic
            self.listener.subscribe('{}/{}/#'.format('common', 'welcome'))  # TODO Dehardcode welcome topic
        else:
            self.listener = mqttsender.Dumb()
        self.sender = mqttsender.Mqtt('syrabond_sender_' + uniqid, config='mqtt.json', clean_session=True)
        confs = common.extract_config('confs.json')
        self.equip_conf_file = confs['equipment']
        config = {}
        for conf in confs:
            config[conf] = common.extract_config((confs[conf]))
            if not config[conf]:
                common.log('Unable to parse configuration file {}. Giving up...'.format(confs[conf]),
                           log_type='error')
                exit()
        for equip in config['equipment']:
            type = config['equipment'][equip]['type']
            group = config['equipment'][equip]['group']
            hrn = config['equipment'][equip]['hrn']
            tags = []
            for tag in config['tags']:
                if equip in config['tags'][tag]:
                    tags.append(tag)
            pir = False
            if 'pir' in config['equipment'][equip]:
                pir = config['equipment'][equip]['pir']
            if config['equipment'][equip]['type'] == 'switch':
                resource = Switch(self.listener, self.sender, self.DB, self.name, equip, type, group, hrn, tags, pir)
            elif config['equipment'][equip]['type'] == 'sensor':
                channels = config['equipment'][equip]['channels']
                resource = Sensor(self.listener, self.sender, self.DB, self.name, equip, type, group, hrn, tags,
                                  pir, channels)
                resource.connect()
            elif config['equipment'][equip]['type'] == 'thermo':
                resource = VirtualAppliance(self.listener, self.sender, self.DB, self.name, equip, type, group,
                                            hrn, tags)
            self.resources[equip] = resource
        for prem in config['premises']:
            for terr in config['premises'][prem]:
                thermo = ambient_sensor = lights = lights_lvl = pres = None
                if 'thermo' in config['premises'][prem][terr]:
                    thermo = self.resources[config['premises'][prem][terr]['thermo']]
                if 'ambient_sensor' in config['premises'][prem][terr]:
                    ambient_sensor = self.resources[config['premises'][prem][terr]['ambient_sensor']]
                if 'lights' in config['premises'][prem][terr]:
                    lights = [self.resources[res] for res in config['premises'][prem][terr]['lights']]
                if 'lights_lvl' in config['premises'][prem][terr]:
                    lights_lvl = self.resources[config['premises'][prem][terr]['lights_lvl']]
                if 'pres' in config['premises'][prem][terr]:
                    pres = self.resources[config['premises'][prem][terr]['pres']]

                premise = Premises(prem, terr, config['premises'][prem][terr]['hrn'],
                                 ambient_sensor, lights, thermo, lights_lvl, pres)
                # todo prohibit "." in the name of terra
                self.premises[prem+'.'+terr] = premise
        for binding in config['bind']:
            prem = config['bind'][binding]
            self.premises[prem].resources.append(self.resources[binding])
            # connecting thermostates
            if self.resources[binding].type == 'thermo':
                self.premises[prem].thermostat = self.resources[binding]
                self.premises[prem].thermostat.topic = (
                        self.premises[prem].thermostat.obj_name
                        + '/' + self.premises[prem].thermostat.type
                        + '/' + prem
                )
                self.premises[prem].thermostat.connect()
        config.clear()

    def get_premises(self, terra=None, code=None, tag=None):
        result = []
        if terra:
            for prem in self.premises:
                if self.premises[prem].terra == terra:
                    result.append(self.premises[prem])
        if code:
            if result:
                for x in result:
                    # todo prohibit doubling codes
                    if x.code == code:
                        result = [x]
        for r in result:
            print(r.terra, r.code, r.name)
        return result

    def get_resource(self, uid=None, group=None, tag=None):
        result = set()
        print()
        if group:
            for res in self.resources:
                if self.resources[res].group == group:
                    result.update({self.resources[res]})
        if uid:
            return self.resources.get(uid, False)
        if tag:
            for res in self.resources:
                if tag in self.resources[res].tags:
                    result.update({self.resources[res]})
        return result

    def state_updated(self, client, userdata, message):
        common.log('New message in topic {}: {}'.format(message.topic, message.payload.decode("utf-8")))
        for res in self.resources:
            if self.resources[res].topic == message.topic:
                self.resources[res].update_state(message.payload.decode("utf-8"))

    def message_handler(self):
        self.listener.message_buffer_lock = True
        if self.listener.message_buffer:
            for n in self.listener.message_buffer:
                print(n)
                type, id, channel = parse_topic(n)
                msg = self.listener.message_buffer[n]
                if channel == 'pir':
                    if self.resources[id].pir_direct:
                        self.resources[id].pir_direct_react(msg)
                elif channel == 'temp' or channel == 'hum':
                    self.resources[id].set_channel_state(channel, msg)
                elif type == 'thermo':
                    self.premises[id].thermostat.update_state(msg)
                elif type == 'status':
                    if id in self.resources:
                        self.resources[id].update_status(msg)
                    else:
                        self.DB.rewrite_quarantine(id, msg)
                elif type == 'welcome':
                        self.DB.rewrite_quarantine(id, msg)

        self.listener.message_buffer.clear()
        self.listener.message_buffer_lock = False

    def add_new_resourse(self, type: str, uid: str, group: str, hrn: str, **kwargs: list) -> bool:

            if type == 'switch':
                print('here1')
                resource = Switch(self.listener, self.sender, self.DB, self.name, uid, type, group, hrn, [], False)
                self.resources[uid] = resource
                print(resource.state)
                resource.update_state('OFF')  # TODO Retrieve real device state
                print('here2')
                print(resource.state)
            elif type == 'sensor':
                channels = kwargs['channels']
                print(uid, type, group, hrn, [], False, channels)
                resource = Sensor(self.listener, self.sender, self.DB, self.name, uid, type, group, hrn, [],
                                  False, channels)
                self.resources[uid] = resource
            self.update_equip_conf()
            return True


    def update_equip_conf(self):
        conf = {}
        for id in self.resources:
            type = channels = group = hrn = pir = None
            res = self.resources[id]
            content = dir(res)
            uid = id
            if 'type' in content:
                type = res.type
            if 'channels' in content:
                channels = res.channels
            if 'group' in content:
                group = res.group
            if 'hrn' in content:
                hrn = res.hrn
            if 'pir' in content:
                pir = res.pir
            conf.update({uid: {'type': type, 'channels': channels, 'group': group, 'hrn': hrn, 'pir': pir}})
        common.rewrite_config(self.equip_conf_file, conf)
        #print(conf)



class Premises:

    def __init__(self, terra, code, name, ambient_sensor, lights, thermo, lights_lvl, pres):
        self.resources = []
        self.terra = terra
        self.code = code
        self.name = name
        self.ambient = self.thermostat = self.lights = None
        if ambient_sensor:
            self.ambient = ambient_sensor
        if thermo:
            self.thermostat = thermo
        if lights:
            self.lights = lights
        self.light_lvl = None
        self.presence = None
        self.ventilation = None


class Resource:
    
    def __init__(self, listener, sender, db, obj_name, uid, type, group, hrn, tags):
        self.uid = uid
        self.type = type
        self.group = group
        self.tags = tags
        self.hrn = hrn
        self.obj_name = obj_name
        self.topic = obj_name+'/'+self.type+'/'+self.uid
        self.sender = sender
        self.listener = listener
        self.DB = db
        self.state = None  # TODO Get from DB on startup. DONE!
        self.DB.check_state_row_exist(self.uid)
        self.init_state()

    def init_state(self):
        self.state = self.get_state()

    def update_state(self, state):
        if not self.state == state:
            self.state = state
            self.DB.rewrite_state(self.uid, self.state)
            common.log('The state of {} ({}) changed to {}'.format(self.uid, self.hrn, self.state))

    def get_state(self):
        return self.DB.read_state(self.uid)[0][0]


class VirtualAppliance(Resource):

    def connect(self):
        self.listener.subscribe(self.topic)

    def set_state(self, state):
        self.update_state(state)
        self.sender.mqttsend(self.topic, state)


class Device(Resource):

    def __init__(self, listener, sender, db, obj_name, uid, type, group, hrn, tags, pir):
        super().__init__(listener, sender, db, obj_name, uid, type, group, hrn, tags)
        self.maintenance_topic = '{}/{}/{}'.format(obj_name, 'management', self.uid)
        self.status_topic = '{}/{}/{}'.format(obj_name, 'status', self.uid)
        self.status = None
        self.pir = pir
        self.DB.check_status_row_exist(self.uid)

        if pir:
            self.pir_topic = self.topic+'/'+pir
            self.listener.subscribe(self.pir_topic)
            self.pir_direct = True

        #--- maintenance commands ---
        # TODO dehardcode and encrypt
        self.repl_on = 'ZAVULON'
        self.repl_off = 'ISAAK'
        self.reboot = 'ZARATUSTRA'
        self.gimme_state = 'STATE'

    def request_state(self):
        try:
            self.sender.mqttsend(self.maintenance_topic, self.get_state)
        except Exception as e:
            print(e)
            return False

    def device_reboot(self):
        try:
            self.sender.mqttsend(self.maintenance_topic, self.reboot)
        except Exception as e:
            print(e)
            return False

    def webrepl(self, command='on'):
        if command == 'on':
            try:
                self.sender.mqttsend(self.maintenance_topic, self.repl_on)
            except Exception as e:
                print(e)
                return False
        elif command == 'off':
            try:
                self.sender.mqttsend(self.maintenance_topic, self.repl_off)
            except Exception as e:
                print(e)
                return False

    def update_status(self, status):
        self.status = status
        self.DB.rewrite_status(self.uid, self.status)


class Switch(Device):

    def toggle(self):
        self.get_state()
        try:
            if self.state == 'ON':
                self.off()
            elif self.state == 'OFF':
                self.on()
            else:
                return False
            return True
        except Exception as e:
            print(e)
            return False

    def turn(self, command):
        try:
            if command.lower() == 'on':
                self.on()
            elif command.lower() == 'off':
                self.off()
            else:
                return False
        except Exception as e:
            print(e)
            return False

    def on(self):
        try:
            self.sender.mqttsend(self.topic, 'on')
            self.update_state('ON')
            return True
        except Exception as e:
            print(e)
            return False

    def off(self):
        try:
            self.sender.mqttsend(self.topic, 'off')
            self.update_state('OFF')
            return True
        except Exception as e:
            print(e)
            return False

    def pir_direct_react(self, cmd):
        if cmd == '1':
            self.on()
        elif cmd == '0':
            self.off()


class Sensor(Device):

    def __init__(self, listener, sender, db, obj_name, uid, type, group, hrn, tags, pir, channels):
        super().__init__(listener, sender, db, obj_name, uid, type, group, hrn, tags, pir)
        self.state = {}
        if isinstance(channels, str):
            self.channels = channels.split(', ')
        else:
            self.channels = channels

    def connect(self):
        for channel in self.channels:
            self.listener.subscribe('{}/{}'.format(self.topic, channel))

    def set_channel_state(self, channel, state):

        if channel not in self.state or self.state[channel] != state:
            self.state.update({channel: state})
            self.update_state(self.state)

    def update_state(self, state):
        state_string = ', '
        state_string = state_string.join([channel+': '+state[channel] for channel in state.keys()])
        self.DB.rewrite_state(self.uid, state_string)
        common.log('The state of {} ({}) changed to {}'.format(self.uid, self.hrn, state_string))

    def get_state(self):
        state_string = self.DB.read_state(self.uid)[0][0]
        splited = [s.split(': ') for s in state_string.split(', ')]
        result = {}
        try:
            [result.update({channel[0]: channel[1]}) for channel in splited]
            return result
        except IndexError:
            return result


def parse_topic(topic):
    type = id = channel = None
    splited = topic.split('/')
    if len(splited) == 4:
        type = topic.split('/')[1]
        id = topic.split('/')[2]
        channel = topic.split('/')[3]
    elif len(splited) == 3:
        type = topic.split('/')[1]
        id = topic.split('/')[2]
    return type, id, channel