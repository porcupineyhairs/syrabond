from syrabond import facility


class API:
    def __init__(self, facility_name, listen=False):
        self.facility = facility.Facility(facility_name, listen=listen)

        self.ACTIONS = {
            'shift': 'shift_resources',
            'state': 'get_state',
            'set': 'shift_prem_property',
            'maintenance': 'maint_device',
            'statusall': 'get_status_all',
            'structure': 'get_struct',
            'conf': 'get_scopes'
        }

        self.GROUPS = set()
        for res in self.facility.resources:
            self.GROUPS.update({self.facility.resources[res].group})
        self.TAGS = set()
        for res in self.facility.resources:
            [self.TAGS.update({x}) for x in self.facility.resources[res].tags]
        self.PREMS = set()
        [self.PREMS.update({x}) for x in self.facility.premises]

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
        if isinstance(attr, facility.VirtualAppliance):
            attr.set_state(value)

    def request_device_state(self, uids, format):
        pass

    def get_status_all(self, null):
        status_all = []
        for r in self.facility.resources:
            res = self.facility.resources[r]
            if isinstance(res, facility.Device):
                for prem in self.facility.premises:
                    premise = self.facility.premises[prem]
                    if res in premise.resources:
                        prem_index = ('{}:{} '.format(premise.terra, premise.code))
                        status_all.append({'uid': res.uid, 'premise': prem_index,
                                           'ip': self.facility.DB.read_status(res.uid)[0][0]})
        return status_all

    def get_resources(self, entities):
        resources = set()
        for one in entities:
            if one in self.facility.resources:
                resources.update({self.facility.resources[one]})
            elif one in self.GROUPS:
                resources.update(self.facility.get_resource(group=one))
            elif one in self.TAGS:
                resources.update(self.facility.get_resource(tag=one))
            elif one in self.PREMS:
                resources.update(self.facility.premises[one].resources)

        return resources

    def get_struct(self, params):
        result = {}
        struct_type = None
        try:
            struct_type = params[0][0]
        except TypeError:
            pass

        if struct_type == 'scopes':
            result.update({'groups': list(self.GROUPS)})
            result.update({'tags': list(self.TAGS)})

        elif struct_type == 'tags':
            return list(self.TAGS)

        elif struct_type == 'groups':
            return list(self.GROUPS)

        elif struct_type == 'premises':
            terras = set()
            [terras.update(self.facility.premises[prem].terra) for prem in self.facility.premises]
            for n in sorted(terras):
                premises = [{'floor': self.facility.premises[prem].terra,
                             'index': prem, 'name': self.facility.premises[prem].name,
                             'ambient': get_uid(self.facility.premises[prem].ambient),
                             'thermostat': get_uid(self.facility.premises[prem].thermostat)}
                            for prem in self.facility.premises if self.facility.premises[prem].terra == n]
                result.update({n: premises})

        elif struct_type == 'quarantine':
            result = []
            response = self.facility.DB.get_quarantine()
            [result.append({'uid': s[0], 'ip': s[1]}) for s in response]

        return result

    def get_structure(self, params):  # TODO To be destroyed
        print(params)
        arg = None
        result = {}
        struct_type = params[0][0]
        if len(params) == 2:
            arg = params[1]
        if struct_type == 'groups':
            if arg:
                if arg in self.GROUPS:
                    result = []
                    resources = self.get_resources([arg])
                    for res in resources:
                        result.append({'uid': res.uid, 'type': res.type, 'name': res.hrn, 'state': res.get_state()})
            else:
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

        elif struct_type == 'tag':
            result = []
            tag_attr = params[1]
            resources = self.get_resources([tag_attr])
            for res in resources:
                result.append({'uid': res.uid, 'type': res.type, 'name': res.hrn, 'state': res.get_state()})

        elif struct_type == 'scopes':
            result = {}
            result.update({'groups': list(self.GROUPS)})
            result.update({'tags': list(self.TAGS)})

        return result

    def get_state(self, params):
        result = []
        entities = params[0]
        resources = self.get_resources(entities)
        for res in resources:
            try:
                prem = [x for x in self.facility.premises.values() if res in x.resources][0]
            except IndexError:
                prem = dumb_prem
                prem.name = self.facility.name
                prem.terra = '0'
            if isinstance(res, facility.Sensor):
                result.append({'uid': res.uid, 'premise': prem.name, 'floor': prem.terra, 'type': res.type,
                               'channels': res.channels, 'name': res.hrn, 'state': res.get_state()})
            else:
                result.append({'uid': res.uid, 'premise': prem.name, 'floor': prem.terra, 'type': res.type,
                               'name': res.hrn, 'state': res.get_state()})
        return result

    def shift_resources(self, params):
        entities = params[0]
        command = params[1]
        resources = self.get_resources(entities)
        for res in resources:
            if isinstance(res, facility.VirtualAppliance):
                try:
                    res.set_state(command.lower())
                except AttributeError:
                    pass
            elif isinstance(res, facility.Switch):
                try:
                    if command.lower() == 'toggle':
                        res.toggle()
                    else:
                        res.turn(command.lower())
                except AttributeError:
                    pass
            elif isinstance(res, facility.Sensor):
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

    def add_device(self, params):
        pass

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


def dumb_prem():
    name = 'hui'
    terra = 'rul'


def get_uid(entity):
    try:
        return entity.uid
    except AttributeError:
        return None