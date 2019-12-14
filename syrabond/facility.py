from syrabond import mqttsender, common, database, orm
from uuid import uuid1
from sys import exit


class Facility:
    """
    The main common class. While initialization it creates instances of all the resources and premises, connects DBO.
    All of resources are stored in dicts.
    """

    def __init__(self, name: str, listen=False):
        self.premises = {}
        self.resources = {}
        self.virtual_apls = {}
        self.tags = {}
        self.name = name
        self.DB = database.Mysql()  # TODO Gonna be deprecated
        self.dbo = orm.DBO('mysql')  # TODO Choose DB interface with config
        self.dbo.truncate_entropy()
        uniqid = str(uuid1())
        common.log('Creating Syrabond instance with uuid ' + uniqid)
        self.welcome_topic = '{}/{}/'.format('common', 'welcome')
        if listen:
            self.listener = mqttsender.Mqtt('syrabond_listener_' + uniqid, config='mqtt.json', clean_session=True)
            self.listener.subscribe('{}/{}/#'.format(self.name, 'status'))  # TODO Dehardcode status topic
            self.listener.subscribe(self.welcome_topic+'#')  # TODO Dehardcode welcome topic
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
        resources_loaded = self.dbo.load_resources()  # Loading resources params from DB and creating instances
        for res in resources_loaded:
            channels = None
            resource = None
            tags = self.dbo.get_tags(res.uid)
            if res.channels:
                channels = res.channels.split(',')
            if res.type == 'switch':
                resource = Switch(self.listener, self.sender, self.name, self.dbo,
                                  res.uid, res.type, res.group, res.hrn, tags, res.pir, channels)
            elif res.type == 'sensor':
                resource = Sensor(self.listener, self.sender, self.name, self.dbo,
                                  res.uid, res.type, res.group, res.hrn, tags, res.pir, channels)
            elif res.type == 'thermo':
                resource = VirtualAppliance(self.listener, self.sender, self.name, self.dbo,
                                            res.uid, res.type, res.group, res.hrn, tags)
            if resource:
                self.resources[res.uid] = resource

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
                        self.name
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
        """Returns the list of resources within specified scope"""
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
        """
        The function to be involved in the main loop of daemon.
        It checks the MQTT message buffer, parse messages and acts depending of content.
        The main goal is to update states in DB.
        After every state msg increase entropy.
        """
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
                elif type == 'switch':
                    self.resources[id].update_state(msg.upper())
                elif type == 'thermo':
                    self.premises[id].thermostat.update_state(msg)
                elif type == 'status':
                    if id in self.resources:
                        self.resources[id].update_status(msg)
                elif type == 'welcome':
                        self.DB.rewrite_quarantine(id, msg)
                if type == 'switch' or type == 'sensor' or type == 'thermo':
                    self.dbo.increase_entropy()
        self.listener.message_buffer.clear()
        self.listener.message_buffer_lock = False

    def add_new_resourse(self, type: str, uid: str, group: str, hrn: str, **kwargs: list) -> bool:
        """Create new resource instance and update config. To be used with API."""
        if type == 'switch':
            resource = Switch(self.listener, self.sender, self.name, self.DB, uid, type, group, hrn, [], False)
            self.resources[uid] = resource
            print(resource.state)
            resource.update_state('OFF')  # TODO Retrieve real device state
        elif type == 'sensor':
            channels = kwargs['channels']
            print(uid, type, group, hrn, [], False, channels)
            resource = Sensor(self.listener, self.sender, self.name, self.DB, uid, type, group, hrn, [],
                              False, channels)
            self.resources[uid] = resource

        self.update_equip_conf()
        self.welcome_new_device(uid)
        return True

    def welcome_new_device(self, uid: str):
        """Initialize new device"""
        self.resources[uid].device_init()
        self.sender.mqttsend(self.welcome_topic+uid, '')  # Empty message to cancel retained
        self.DB.del_from_quarantine(uid)

    def update_device(self, uid):
        """Update device properties via ORM"""
        res = self.resources[uid]
        self.dbo.update_resource_properties(res)

    def update_equip_conf(self):  # TODO Change and use only for backup purposes
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


class Premises:
    """
    The class to represent facility's premises.
    The properties are:
    terra: floor or another type of detached space;
    code: index of the premise within the terra;
    name: human readable name of premise
    ambient_sensor, lights, thermo, lights_lvl, pres: premise's dedicated sensors for specified params
    """

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
    """
    The class to represent appliances.
    The properties are:
    listener: instance of mqttsender to deliver the messages;
    sender: instance of mqttsender to send the messages;
    basename: code name of facility to be used as base to build the names of MQTT topics;
    db: dbo object to connect with;
    uid: unique identifier;
    type: the type of appliance (switch, sensor, etc);
    group: the main group of appliance;
    hrn: human readable name;
    tags: list of associated tags.
    """
    
    def __init__(self, listener, sender, basename, dbo, uid, type, group, hrn, tags):
        self.uid = uid
        self.type = type
        self.group = group
        self.tags = tags
        self.hrn = hrn
        self.topic = basename+'/'+self.type+'/'+self.uid
        self.sender = sender
        self.listener = listener
        self.dbo = dbo
        self.state = None
        self.check_state()

    def check_state(self):
        self.state = self.get_state()

    def update_state(self, state):
        if not self.state == state:
            self.state = state
            self.dbo.update_state(self.uid, self.state)
            common.log('The state of {} ({}) changed to {}'.format(self.uid, self.hrn, self.state))

    def get_state(self):
        return self.dbo.get_state(self.uid)


class VirtualAppliance(Resource):
    """
    The inheritor class to represent appliances without physical body.
    Useful for thermostat or other level-control setters.
    """
    def connect(self):
        self.listener.subscribe(self.topic)

    def set_state(self, state):
        self.update_state(state)
        self.sender.mqttsend(self.topic, state)


class Device(Resource):
    """
    The inheritor class to represent physical devices.
    Additional properties:
    pir: is it movement detector onboard?
    channels: list of channels to receive commands (for switches) of to send measurements.
    """
    def __init__(self, listener, sender, basename, db, uid, type, group, hrn, tags, pir, channels):
        super().__init__(listener, sender, basename, db, uid, type, group, hrn, tags)
        self.maintenance_topic = '{}/{}/{}'.format(basename, 'management', self.uid)
        self.status_topic = '{}/{}/{}'.format(basename, 'status', self.uid)
        self.status = None
        self.pir = pir
        self.channels = channels
        self.connect()

        if pir:
            self.pir_topic = self.topic+'/'+'pir'  # TODO Dehardcode
            self.listener.subscribe(self.pir_topic)
            self.pir_direct = True

        #--- maintenance commands ---
        # TODO dehardcode and encrypt
        self.repl_on = 'ZAVULON'
        self.repl_off = 'ISAAK'
        self.reboot = 'ZARATUSTRA'
        self.gimme_state = 'STATE'
        self.init = 'INITIALIZE'

    def connect(self):
        """Will be used in children classes"""
        pass

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

    def device_init(self):
        try:
            self.sender.mqttsend(self.maintenance_topic, self.init)
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
        self.dbo.update_status(self.uid, self.status)


class Switch(Device):
    """Class to represent switches"""

    def connect(self):
        self.listener.subscribe(self.topic)

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
    """Class to represent sensors"""
    def __init__(self, listener, sender, basename, dbo, uid, type, group, hrn, tags, pir, channels):
        super().__init__(listener, sender, basename, dbo, uid, type, group, hrn, tags, pir, channels)
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
        self.dbo.update_state(self.uid, state_string)
        common.log('The state of {} ({}) changed to {}'.format(self.uid, self.hrn, state_string))

    def get_state(self):
        result = {}
        state_string = self.dbo.get_state(self.uid)
        if state_string:
            splited = [s.split(': ') for s in state_string.split(', ')]
            try:
                [result.update({channel[0]: channel[1]}) for channel in splited]
            except IndexError:
                pass
        return result


def parse_topic(topic: str):
    """Split topic by / sign and return touple of type, id and channel"""
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