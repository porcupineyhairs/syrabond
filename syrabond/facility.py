from uuid import uuid1
from sys import exit

from syrabond import mqttsender, common, orm, automation, homekit


class Facility:
    """
    The main common class. While initialization it creates instances of all the resources and premises, connects DBO.
    All of resources are being stored in dict.
    """

    def __init__(self, name: str, listen=False, **kwargs):
        self.premises = {}
        self.resources = {}
        self.virtual_apls = {}
        self.tags = {}
        self.addons={}
        self.name = name
        uid = str(uuid1())
        self.dbo = orm.DBO('mysql')  # TODO Choose DB interface with config
        common.log('Creating Syrabond instance with uuid ' + uid)
        self.welcome_topic = '{}/{}/'.format('common', 'welcome')
        if listen:
            self.listener = mqttsender.Mqtt('syrabond_listener_' + __name__, config='mqtt.json', clean_session=False)
            self.listener.subscribe('{}/{}/#'.format(self.name, 'status'))  # TODO Dehardcode status topic
            self.listener.subscribe(self.welcome_topic+'#')  # TODO Dehardcode welcome topic
        else:
            self.listener = mqttsender.Dumb()
        self.sender = mqttsender.Mqtt('syrabond_sender_' + uid, config='mqtt.json', clean_session=True)

        Resource.basename = name
        Resource.dbo = self.dbo
        Resource.listener = self.listener
        Resource.sender = self.sender

        confs = common.extract_config('confs.json')
        self.equip_conf_file = confs['equipment']
        config = {}
        for conf in confs:
            config[conf] = common.extract_config((confs[conf]))
            if not config[conf]:
                common.log('Unable to parse configuration file {}. Giving up...'.format(confs[conf]),
                           log_type='error')
                exit()
        self.build_resources()
        self.build_scenarios()
        self.build_premises(config['premises'])
        self.build_bindings(config['bind'])

        if 'addons' in kwargs:
            if 'homekit' in kwargs['addons']:
                home_kit = homekit.HomeKit(self)
                self.addons.update({'homekit': home_kit})
                home_kit.run()

        config.clear()

    def __repr__(self):
        return f'Syrabond facility \"{self.name}\" containing {self.resources.__len__()} resources'

    def shutdown(self):
        if isinstance(self.listener, mqttsender.Mqtt):
            self.listener.disconnect()
        self.dbo.connection.close()
        if 'homekit' in self.addons:
            self.addons['homekit'].driver.stop()
            self.addons['homekit'].driver_thread.join()

    def build_resources(self):
        resources_loaded = self.dbo.load_resources()  # Loading resources params from DB and creating instances
        for res in resources_loaded:
            channels = None
            resource = None
            tags = self.dbo.get_tags(res.uid)
            if res.channels:
                channels = res.channels.split(',')
            if res.type == 'switch':
                resource = Switch(res.uid, res.type, res.group, res.hrn, tags, res.pir, channels)
            elif res.type == 'sensor':
                resource = Sensor(res.uid, res.type, res.group, res.hrn, tags, res.pir, channels)
            elif res.type == 'thermo':
                resource = VirtualAppliance(res.uid, res.type, res.group, res.hrn, tags)
            if resource:
                self.resources[res.uid] = resource

    def build_scenarios(self):
        scenarios_loaded = self.dbo.load_scenarios('cond')  # TODO Dehardcode
        for scen in scenarios_loaded:
            if scen['type'] == 'cond':
                conditions = {}
                effect = []
                id = scen['id']
                active = scen['active']
                hrn = scen['hrn']
                for cond_conf in scen['conditions']:
                    res = cond_conf.resource
                    id = cond_conf.id
                    cond = automation.Conditions(
                        id, self.resources[res], cond_conf.positive, cond_conf.compare, cond_conf.state)
                    conditions.update({res: cond})
                for effect_conf in scen['effect']:
                    res = effect_conf.resource
                    eff = automation.Map(self.resources[res], effect_conf.state)
                    effect.append(eff)
                scn = automation.Scenario(id, active, hrn, conditions, effect)
                for cond in scn.conditions:
                    scn.conditions[cond].resource.scens.update({id: scn})

    def build_premises(self, config):
        for prem in config:
            for terr in config[prem]:
                thermo, ambient_sensor, lights, lights_lvl, presence, vent = None, None, None, None, None, None
                if 'thermo' in config[prem][terr]:
                    thermo = self.resources[config[prem][terr]['thermo']]
                    thermo.connect()
                if 'ambient_sensor' in config[prem][terr]:
                    ambient_sensor = self.resources[config[prem][terr]['ambient_sensor']]
                if 'lights' in config[prem][terr]:
                    lights = [self.resources[res] for res in config[prem][terr]['lights']]
                if 'lights_lvl' in config[prem][terr]:
                    lights_lvl = self.resources[config[prem][terr]['lights_lvl']]
                if 'presence' in config[prem][terr]:
                    presence = self.resources[config[prem][terr]['presence']]
                if 'vent' in config[prem][terr]:
                    vent = self.resources[config[prem][terr]['vent']]

                premise = Premise(prem, terr, config[prem][terr]['hrn'],
                                  ambient_sensor=ambient_sensor, lights=lights, thermo=thermo,
                                  lights_lvl=lights_lvl, presence=presence, vent=vent)
                self.premises[f'{prem}.{terr}'] = premise  # todo prohibit "." in the name of terra (frontend)

    def build_bindings(self, config):
        for binding in config:
            prem = config[binding]
            self.premises[prem].resources.append(self.resources[binding])
        unplaced = Premise('niente', 'no', 'nowhere')  # Null Object for unplaced resources
        self.premises[f'{unplaced.code}.{unplaced.terra}'] = unplaced
        placed_resources = {x for y in self.premises.values() for x in y.resources}
        [unplaced.resources.append(res) for res in self.resources.values() if res not in placed_resources]

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
        if isinstance(self.listener, mqttsender.Dumb):
            return None
        while self.listener.message_buffer.size:
            payload = self.listener.message_buffer.dequeue()
            type, id, channel = parse_topic(payload[0])
            msg = payload[1]
            if channel == 'pir':
                if self.resources[id].pir_direct:
                    self.resources[id].pir_direct_react(msg)
            elif channel == 'temp' or channel == 'hum':
                self.resources[id].set_channel_state(channel, msg)
            elif type == 'switch':
                self.resources[id].update_state(msg.upper())
            elif type == 'thermo':
                self.resources[id].update_state(msg)
            elif type == 'status':
                if id in self.resources:
                    self.resources[id].update_status(msg)
            elif type == 'welcome':
                self.dbo.put_quarantine(id, msg)


    def welcome_new_device(self, uid: str):
        """Initialize new device"""
        self.resources[uid].device_init()
        self.sender.mqttsend(self.welcome_topic+uid, '')  # Empty message to cancel retained
        self.DB.del_from_quarantine(uid)


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


class Premise:
    """
    The class to represent facility's premises.
    The properties are:
    terra: floor or another type of detached space;
    code: index of the premise within the terra;
    name: human readable name of premise
    ambient_sensor, lights, thermo, lights_lvl, pres: premise's dedicated sensors for specified params
    """

    def __init__(self, terra, code, name,
                 ambient_sensor=None, lights=None, thermo=None, lights_lvl=None, presence=None, vent=None):
        self.resources = []
        self.terra = terra
        self.code = code
        self.name = name
        self.ambient = ambient_sensor
        self.thermostat = thermo
        self.lights = lights
        self.light_lvl = lights_lvl
        self.presence = presence
        self.ventilation = vent


class Control:
    """
    Non-MQTT virtual control appliances.
    Useful for UI elements to represent automation conditions.
    """

    def __init__(self, uid, type, hrn):
        self.uid = uid
        self.type = type
        self.hrn = hrn
        self.state = None


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

    listener, sender, dbo, basename = None, None, None, 'default'

    def __init__(self, uid, type, group, hrn, tags):
        self.uid = uid
        self.type = type
        self.group = group
        self.tags = tags
        self.hrn = hrn
        self.topic = Resource.basename+'/'+self.type+'/'+self.uid
        self.sender = Resource.sender
        self.listener = Resource.listener
        self.dbo = Resource.dbo
        self.state = None
        self.scens = dict()
        self.check_state()

    def __repr__(self):
        return f'{self.type} uid = {self.uid} \"{self.hrn}\"'

    def check_state(self):
        self.state = self.get_state()

    def update_state(self, state):
        if not self.state == state:
            self.state = state
            self.dbo.update_state(self.uid, self.state)
            common.log(f'The state of {self} changed to {state}')

    def get_state(self):
        return self.dbo.get_state(self.uid)

    def save_config(self):
        """ Rewrite all the properties via ORM"""
        self.dbo.update_resource_properties(self)


class VirtualAppliance(Resource):
    """
    The inheritor class to represent appliances without physical body.
    Useful for thermostat or other level-control setters.
    """
    def connect(self):
        self.listener.subscribe(self.topic)

    def set_state(self, state):
        self.update_state(state)
        self.sender.mqttsend(self.topic, state, retain=True)


class Device(Resource):
    """
    The inheritor class to represent physical devices.
    Additional properties:
    pir: is it movement detector onboard?
    channels: list of channels to receive commands (for switches) of to send measurements.
    """
    def __init__(self, uid, type, group, hrn, tags, pir, channels):
        super().__init__(uid, type, group, hrn, tags)
        self.maintenance_topic = '{}/{}/{}'.format(self.basename, 'management', self.uid)
        self.status_topic = '{}/{}/{}'.format(self.basename, 'status', self.uid)
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

    def __init__(self, uid, type, group, hrn, tags, pir, channels):
        super(Switch, self).__init__(uid, type, group, hrn, tags, pir, channels)

    # Mapping 'what-to-send': 'what-to-store'
    command_map = {
        'off': 'OFF',
        'on': 'ON'
    }

    """Class to represent switches"""

    def update_state(self, state):
        if not self.state == state:
            self.state = state
            self.dbo.update_state(self.uid, self.state)
            common.log(f'The state of {self} changed to {state}')
            for scen in self.scens.values():
                if scen.check_conditions(self) and scen.active:
                    scen.workout()

    def connect(self):
        self.listener.subscribe(self.topic)

    def toggle(self):
        self.get_state()
        try:
            if self.state == Switch.command_map['on']:
                self.off()
            elif self.state == Switch.command_map['off']:
                self.on()
            else:
                return False
            return True
        except Exception as e:
            common.log(f'Error while toggling {self.uid}: {e}')
            return False

    def turn(self, command):
        try:
            if command.lower() == 'on':
                self.on()
            elif command.lower() == 'off':
                self.off()
            elif command.lower() == 'toggle':
                self.toggle()
            else:
                return False
            return True
        except Exception as e:
            common.log(f'Error while turning {self.uid} {command}: {e}')
            return False

    def on(self):
        try:
            self.sender.mqttsend(self.topic, 'on', retain=True)
            self.update_state(Switch.command_map['on'])
            return True
        except Exception as e:
            common.log(f'Error while turning {self.uid} on: {e}')
            return False

    def off(self):
        try:
            self.sender.mqttsend(self.topic, 'off', retain=True)
            self.update_state(Switch.command_map['off'])
            return True
        except Exception as e:
            common.log(f'Error while turning {self.uid} off: {e}')
            return False

    def pir_direct_react(self, cmd):
        if cmd == '1':
            self.on()
        elif cmd == '0':
            self.off()


class Sensor(Device):
    """Class to represent sensors"""
    def __init__(self, uid, type, group, hrn, tags, pir, channels):
        super().__init__(uid, type, group, hrn, tags, pir, channels)
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
        common.log(f'The state of {self} changed to {state_string}')

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