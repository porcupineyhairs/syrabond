from syrabond import facility


class API:
    def __init__(self, facility_name, listen=False):
        self.facility = facility.Facility(facility_name, listen=listen)

        self.GET_ACTIONS = {
            'shift': 'shift_resources',
            'state': 'get_state',
            'set': 'shift_prem_property',
            'maintenance': 'maint_device',
            'statusall': 'get_status_all',
            'structure': 'get_struct',
            'conf': 'get_scopes'
        }

        self.POST_ACTIONS = {
            'add': 'add_entity',
            'premise': 'get_state',
            'edit': 'edit_entity',
            'delete': 'del_entity'
        }

        self.GROUPS = set()
        for res in self.facility.resources:
            self.GROUPS.update({self.facility.resources[res].group})
        self.TAGS = set()
        for res in self.facility.resources:
            [self.TAGS.update({x}) for x in self.facility.resources[res].tags]
        self.PREMS = set()
        [self.PREMS.update({x}) for x in self.facility.premises]
        self.TYPES = set()
        [self.TYPES.update({self.facility.resources[res].type}) for res in self.facility.resources]
        self.SENSOR_CHANNELS = set()
        [self.SENSOR_CHANNELS.update(self.facility.resources[x].channels)
         for x in self.facility.resources if self.facility.resources[x].type == 'sensor']

    def is_consistent_api_request(self, agr):
        try:
            if isinstance(agr, tuple) and len(agr) >= 2:
                if agr[0][0] in self.GET_ACTIONS or agr[0][0] in self.POST_ACTIONS:
                    return True
            else:
                return False
        except ValueError:
            return False

    def get_direct(self, keyword, entities, param):
        method = self.GET_ACTIONS[keyword]
        return getattr(self, method)((entities, param))

    def post_direct(self, action, keyword, data):
        if action in self.POST_ACTIONS and is_correct_post_params(data):
            method = self.POST_ACTIONS[action]
            getattr(self, method)(keyword, data)

    def parse_request(self, request):
        entities = param = None
        if request:
            args = [s.strip().lower() for s in request.split('/')]
            keyword = args[0].lower()
            if keyword in self.GET_ACTIONS:
                if len(args) > 1:
                    entities = [s.lower().strip() for s in args[1].split(',')]
                    if len(args) > 2:
                        param = args[2].lower()
                return {'response': self.get_direct(keyword, entities, param)}
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
        facility_resources = self.facility.resources.copy()
        for r in facility_resources:
            res = facility_resources[r]
            if isinstance(res, facility.Device):
                status_all.append({'uid': res.uid, 'name': res.hrn, 'ip': self.facility.DB.read_status(res.uid)[0][0]})
        return status_all

    def get_resources(self, entities):
        resources = set()
        facility_resources = self.facility.resources.copy()
        facility_premises = self.facility.premises.copy()
        for one in entities:
            if one in facility_resources:
                resources.update({facility_resources[one]})
            elif one in self.GROUPS:
                resources.update(self.facility.get_resource(group=one))
            elif one in self.TAGS:
                resources.update(self.facility.get_resource(tag=one))
            elif one in self.PREMS:
                resources.update(facility_premises[one].resources)
        facility_resources.clear()
        facility_premises.clear()

        return resources

    def get_struct(self, params):
        result = {}
        struct_type = None
        try:
            struct_type = params[0][0]
        except TypeError:
            pass

        if struct_type == 'scopes':
            print(self.TAGS)
            result.update({'groups': list(self.GROUPS)})
            result.update({'tags': list(self.TAGS)})
            result.update({'types': list(self.TYPES)})

        elif struct_type == 'tags':
            return list(self.TAGS)

        elif struct_type == 'groups':
            return list(self.GROUPS)

        elif struct_type == 'types':
            return list(self.TYPES)

        elif struct_type == 'channels':
            return list(self.SENSOR_CHANNELS)

        elif struct_type == 'premises':
            terras = set()
            facility_premises = self.facility.premises.copy()
            [terras.update(facility_premises[prem].terra) for prem in facility_premises]
            for n in sorted(terras):
                premises = [{'floor': facility_premises[prem].terra,
                             'index': prem, 'name': facility_premises[prem].name,
                             'ambient': get_uid(facility_premises[prem].ambient),
                             'thermostat': get_uid(facility_premises[prem].thermostat)}
                            for prem in facility_premises if facility_premises[prem].terra == n]
                result.update({n: premises})
            facility_premises.clear()

        elif struct_type == 'quarantine':
            result = []
            response = self.facility.DB.get_quarantine()
            [result.append({'uid': s[0], 'ip': s[1]}) for s in response]

        elif struct_type in self.facility.resources:
            res = self.facility.resources[struct_type]
            try:
                prem = [x for x in self.facility.premises.values() if res in x.resources][0]
            except IndexError:
                prem = dumb_prem
                prem.name = 'nowhere'
                prem.terra = 'niente'
                prem.code = 'no'
            if isinstance(res, facility.Sensor):
                result = {'uid': res.uid, 'premise': prem.name, 'floor': prem.terra, 'code': prem.code,
                               'type': res.type, 'channels': res.channels, 'name': res.hrn,
                               'group': res.group, 'tags': res.tags}
            else:
                result = {'uid': res.uid, 'premise': prem.name, 'floor': prem.terra, 'code': prem.code,
                               'type': res.type, 'name': res.hrn, 'group': res.group, 'tags': res.tags}

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
                prem.name = 'nowhere'
                prem.terra = 'niente'
                prem.code = 'no'
            prem_index = '{}:{}'.format(prem.terra, prem.code)
            if isinstance(res, facility.Sensor):
                result.append({'uid': res.uid, 'premise': prem.name, 'prem_index': prem_index, 'type': res.type,
                               'channels': res.channels, 'name': res.hrn, 'state': res.get_state()})
            else:
                result.append({'uid': res.uid, 'premise': prem.name, 'prem_index': prem_index, 'type': res.type,
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

    def add_entity(self, entity, data):
        if entity == 'device':
            return self.add_device(data)

    def edit_entity(self, entity, data):
        if entity == 'device':
            return self.edit_device(data)

    def del_entity(self, entity, data):
        if entity == 'device':
            return self.delete_device(data)

    def add_device(self, data):
        device_params = parse_form_json(data)
        result = False
        print(device_params)
        if self.is_correct_new_device_params(device_params):
            if 'channels' in device_params:
                result = self.facility.add_new_resourse(
                    device_params['type'], device_params['uid'], device_params['group'],
                    device_params['hrn'], channels=device_params['channels'])
            else:
                result = self.facility.add_new_resourse(
                    device_params['type'], device_params['uid'], device_params['group'],
                    device_params['hrn'])
        return result

    def edit_device(self, data):  # TODO add result
        device_params = parse_form_json(data)
        print(device_params)
        if self.is_correct_exist_device_params(device_params):
            self.facility.resources[device_params['uid']].group = device_params['group']
            self.facility.resources[device_params['uid']].hrn = device_params['name']
            if 'tags' in device_params:
                self.facility.resources[device_params['uid']].tags = device_params['tags']
            else:
                self.facility.resources[device_params['uid']].tags = []
        self.facility.update_equip_conf()

    def delete_device(self, data):  # TODO add result
        device_params = parse_form_json(data)
        uid = device_params['uid']
        self.facility.resources.pop(uid)
        self.facility.DB.del_resource_rows(uid)
        self.facility.update_equip_conf()

    def is_correct_new_device_params(self, data):
        if 'uid' and 'type' and 'group' in data:
            if data['type'] in self.TYPES and data['group'] in self.GROUPS:
                if not data['uid'] in self.facility.resources:
                    return True
        return False

    def is_correct_exist_device_params(self, data):
        if 'uid' and 'group' in data:
            if data['uid'] in self.facility.resources and data['group'] in self.GROUPS:
                return True
        return False


def check_states(resources):
    result = {}
    for res in resources:
        result.update({res.uid: res.get_state()})
    return result


def dumb_prem():
    name = 'nowhere'
    terra = 'niente'


def get_uid(entity):
    try:
        return entity.uid
    except AttributeError:
        return None


def parse_form_json(data):
    params = {}
    tags = []
    for param in data:
        key = list(param.values())[0]
        value = list(param.values())[1]
        if key == 'tag':
            tags.append(value)
        else:
            params.update({key: value})
    if tags:
        params.update({'tags': tags})
    return params


def is_correct_post_params(data):
    if isinstance(data, list):
        check = set()
        check.update([isinstance(x, dict) for x in data])
        if False in check:
            return False
        check.clear()
        [check.update(x.keys()) for x in data]
        if not len(check) == 2 and 'value' in check and 'name' in check:
            return False
    else:
        return False
    return True




