import mqttsender
from uuid import uuid1
from sys import exit
import syracommon
import syradatabase


class Facility:

    def __init__(self, name, listen=True):
        self.premises = {}
        self.resources = {}
        self.virtual_apls = {}
        self.tags = {}
        self.name = name
        self.DB = syradatabase.Mysql()  # TODO Choose DB interface with config
        uniqid = str(uuid1())
        syracommon.log('Creating Syrabond instance with uuid ' + uniqid)
        if listen:
            self.listener = mqttsender.Mqtt('syrabond_listener_'+uniqid, config='mqtt.json', clean_session=True)
            self.listener.subscribe('{}/{}/#'.format(self.name, 'status'))  # TODO Dehardcode status topic
        else:
            self.listener = mqttsender.Dumb()
        self.sender = mqttsender.Mqtt('syrabond_sender_'+uniqid, config='mqtt.json', clean_session=True)
        confs = syracommon.extract_config('confs.json')
        config = {}
        for conf in confs:
            config[conf] = syracommon.extract_config((confs[conf]))
            if not config[conf]:
                syracommon.log('Unable to parse configuration file {}. Giving up...'.format(confs[conf]),
                               log_type='debug')
                exit()
        for equip in config['equipment']:
            pir = False
            if 'pir' in config['equipment'][equip]:
                pir = config['equipment'][equip]['pir']
            if config['equipment'][equip]['type'] == 'switch':

                resource = Switch(self.listener, self.sender, self.DB, self.name, equip,
                                  config['equipment'][equip]['type'],
                                  config['equipment'][equip]['group'], config['equipment'][equip]['hrn'], pir)
            elif config['equipment'][equip]['type'] == 'sensor':
                resource = Sensor(self.listener, self.sender, self.DB, self.name, equip,
                                  config['equipment'][equip]['type'],
                                  config['equipment'][equip]['group'], config['equipment'][equip]['hrn'], pir,
                                  config['equipment'][equip]['channels'])
                resource.connect()
            elif config['equipment'][equip]['type'] == 'thermo':
                resource = VirtualAppliance(self.listener, self.sender, self.DB, self.name, equip,
                                            config['equipment'][equip]['type'],
                                            config['equipment'][equip]['group'], config['equipment'][equip]['hrn'])
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

    def get_resource(self, uid=None, group=None):
        result = set()
        if group:
            for res in self.resources:
                if self.resources[res].group == group:
                    result.update({self.resources[res]})
            return result
        if uid:
            return self.resources.get(uid, False)

    def state_updated(self, client, userdata, message):
        syracommon.log('New message in topic {}: {}'.format(message.topic, message.payload.decode("utf-8")))
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

        self.listener.message_buffer.clear()
        self.listener.message_buffer_lock = False


    def add_new_resourse(self):
        pass


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
    
    def __init__(self, listener, sender, db, obj_name, uid, type, group, hrn):
        self.uid = uid
        self.type = type
        self.group = group
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
            syracommon.log('The state of {} ({}) changed to {}'.format(self.uid, self.hrn, self.state))

    def get_state(self):
        return self.DB.read_state(self.uid)[0][0]


class VirtualAppliance(Resource):

    def connect(self):
        self.listener.subscribe(self.topic)

    def set_state(self, state):
        self.update_state(state)
        self.sender.mqttsend(self.topic, state)


class Device(Resource):

    def __init__(self, listener, sender, db, obj_name, uid, type, group, hrn, pir):
        super().__init__(listener, sender, db, obj_name, uid, type, group, hrn)
        self.maintenance_topic = '{}/{}/{}'.format(obj_name, 'management', self.uid)
        self.status_topic = '{}/{}/{}'.format(obj_name, 'status', self.uid)
        self.status = None
        self.pir = pir

        self.DB.check_status_row_exist(self.uid)
        # self.listener.subscribe(self.status_topic) Deprecated. Now subscribing to ../status/#

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

    def __init__(self, listener, sender, db, obj_name, uid, type, group, hrn, pir, channels):
        super().__init__(listener, sender, db, obj_name, uid, type, group, hrn, pir)
        self.state = {}
        if channels.find(', ') > 0:
            self.channels = channels.split(', ')
        else:
            self.channels = [channels]

    def connect(self):
        for channel in self.channels:
            self.listener.subscribe('{}/{}'.format(self.topic, channel))

    def set_channel_state(self, channel, state):

        if channel not in self.state or self.state[channel] != state:
            self.state.update({channel: state})
            state_string = ''
            for x in self.state:
                state_string += '{}: {}, '.format(x, self.state[x])
            self.update_state(state_string.rstrip(', '))
        # TODO Update states in Web interface, database, etc.

    def update_state(self, state):
        self.DB.rewrite_state(self.uid, state)
        syracommon.log('The state of {} ({}) changed to {}'.format(self.uid, self.hrn, state))


class API:
    def __init__(self, facility_name, listen=False):
        self.facility = Facility(facility_name, listen=listen)

        self.ACTIONS = {
            'shift': 'shift_resources',
            'state': 'get_state',
            'set': 'shift_prem_property',
            'maintenance': 'maint_device',
            'statusall': 'get_status_all',
            'structure': 'get_structure'
            }

        self.GROUPS = set()
        for res in self.facility.resources:
            self.GROUPS.update({self.facility.resources[res].group})

    def is_consistent_api_request(self, agr):
        try:
            if isinstance(agr, tuple) and len(agr) >= 2:
                if agr[0][0] in self.ACTIONS:
                    return True
            else:
                return False
        except ValueError:
            return False

    def direct(self, keyword, entities, param):
        method = self.ACTIONS[keyword]
        return getattr(self, method)((entities, param))

    def parse_request(self, request):
        entities = param = None
        if request:
            args = [s.strip().lower() for s in request.split('/')]
            keyword = args[0].lower()
            if keyword in self.ACTIONS:
                if len(args) > 1:
                    entities = [s.lower().strip() for s in args[1].split(',')]
                    if len(args) > 2:
                        param = args[2].lower()
                return {'response': self.direct(keyword, entities, param)}
            else:
                return {'response': 'bad request'}, 400
        else:
            return {'response': 'empty request'}, 400

    def shift_prem_property(self, premise_property, value):
        premise_index = premise_property.split(' ')[0]
        property = premise_property.split(' ')[1]
        attr = getattr(self.facility.premises[premise_index], property)
        if isinstance(attr, list):
            for each in attr:
                getattr(each, 'turn')(value.lower())
        if isinstance(attr, VirtualAppliance):
            attr.set_state(value)

    def request_device_state(self, uids, format):
        pass

    def get_status_all(self, null):
        status_all = []
        for r in self.facility.resources:
            res = self.facility.resources[r]
            if isinstance(res, Device):
                for prem in self.facility.premises:
                    premise = self.facility.premises[prem]
                    if res in premise.resources:
                        prem_index = ('{}:{} '.format(premise.terra, premise.code))
                        status_all.append({'uid': res.uid,
                                                    'premise': prem_index,
                                                    'ip': self.facility.DB.read_status(res.uid)[0][0]
                                                       })
        return status_all

    def get_resources(self, entities):
        resources = set()
        for one in entities:
            if one in self.facility.resources:
                resources.update({self.facility.resources[one]})
            elif one in self.GROUPS:
                resources.update(self.facility.get_resource(self.facility, group=one))
        return resources

    def get_structure(self, params):
        result = {}
        struct_type = params[0][0]
        if struct_type == 'groups':
            for group in self.GROUPS:
                resources = self.get_resources([group])
                res_list = []
                for res in resources:
                    res_list.append({'uid': res.uid, 'type': res.type, 'name': res.hrn, 'state': res.get_state()})
                result.update({group: res_list})
        elif struct_type == 'thermo':
            for prem in self.facility.premises:
                premise = self.facility.premises[prem]
                try:
                    result.update({prem: {'name': premise.name, 'thermostat_id': premise.thermostat.uid,
                                   'thermostat_state': premise.thermostat.state}})
                except:
                    continue
        elif struct_type == 'quarantine':
            result = []
            response = self.facility.DB.get_quarantine()
            [result.append({'uid': s[0], 'ip': s[1]}) for s in response]
        return result

    def get_state(self, params):
        entities = params[0]
        resources = self.get_resources(entities)
        return check_states(resources)

    def shift_resources(self, params):
        entities = params[0]
        command = params[1]
        resources = self.get_resources(entities)
        for res in resources:
            if isinstance(res, VirtualAppliance):
                try:
                    res.set_state(command.lower())
                except AttributeError:
                    pass
            elif isinstance(res, Switch):
                try:
                    if command.lower() == 'toggle':
                        res.toggle()
                    else:
                        res.turn(command.lower())
                except AttributeError:
                    pass
            elif isinstance(res, Sensor):
                try:
                    res.update_state(command.lower())
                except AttributeError:
                    pass
        return check_states(resources)

    def maint_device(self, params):
        MAINT_COMMANDS = {
            "reboot": "device_reboot",
            "repl": "webrepl"
        }
        entities = params[0]
        command = params[1]
        resources = self.get_resources(entities)
        for res in resources:
            if command in MAINT_COMMANDS:
                    getattr(res, MAINT_COMMANDS[command])()

        return check_states(resources)

    def check_for_newbies(self):
        self.facility.listener.subscribe(self.facility.name+'/status/#')



def check_states(resources):
    result = {}
    for res in resources:
        result.update({res.uid: res.get_state()})
    return result


def parse_topic(topic):
    type = topic.split('/')[1]
    id = topic.split('/')[2]
    channel = None
    if len(topic.split('/')) == 4:
        channel = topic.split('/')[3]
    return type, id, channel

