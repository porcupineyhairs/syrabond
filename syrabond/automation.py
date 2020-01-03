import time
import syrabond.facility
from syrabond.common import log

#  TODO: 1) For each scenario should be 2 subscenarios: start and finish;les
#  TODO  2) Daemon should reload scenarioss from DB each ~hour


class StateEngine:
    def __init__(self):
        self.resources = {}


class TimeEngine:
    def __init__(self, facility, orm):
        self.scenarios = []
        scens = orm.load_scenarios('time')
        for scen in scens:
            effect = []
            schedule = []
            active = scen['active']
            for schedule_conf in scen['schedule']:
                schedule.append(self.Schedule(schedule_conf))
            for effect_conf in scen['effect']:
                res = effect_conf.resource
                eff = Map(facility.resources[res], effect_conf.state)
                effect.append(eff)
            self.scenarios.append(self.Scenario(active, scen['hrn'], schedule, effect))
        log('TimeEngine engaged.')

    def add_scen(self):
        pass

    def check_shedule(self):
        result = []
        now = {'weekday': time.localtime(time.time()).tm_wday,
               'time': [time.localtime(time.time()).tm_hour, time.localtime(time.time()).tm_min]}
        print(now)
        for scen in self.scenarios:
            for schedule in scen.schedule:
                print(schedule.weekdays, schedule.start_time)
                if now['weekday'] in schedule.weekdays and scen.active:
                    if now['time'] == schedule.start_time:
                        result.append(scen)
        return result

    class Schedule:
        def __init__(self, schedule):
            self.weekdays = [int(x) for x in schedule.weekdays.split(',')]
            self.start_time = [int(x) for x in schedule.start.split(',')]

    class Scenario:
        def __init__(self, active, hrn, schedule, effect):
            self.type = 'time'
            self.active = active
            self.hrn = hrn
            self.schedule = schedule
            self.effect = effect
            self.ran = None

        def workout(self):
            now = (time.localtime(time.time()).tm_yday,
                   time.localtime(time.time()).tm_hour,
                   time.localtime(time.time()).tm_min)
            if not self.ran == now:
                log(f"TimeEngine: Running scenario: {self.hrn}")
                self.ran = now
                for mapper in self.effect:
                    mapper.activate()


class Scenario:  # TODO Add comparison rules for conditions (and | or)

    def __init__(self, active: bool, hrn: str, conditions, effect):
        self.type = 'cond'
        self.active = active
        self.hrn = hrn
        self.conditions = conditions
        self.effect = effect

    def check_conditions(self, resource):
        result = set()
        if self.conditions[resource.uid].check():
            for cond in self.conditions:
                result.add(self.conditions[cond].check())
            if result == {True}:
                return True
            else:
                return False
        else:
            return False

    def workout(self):
        for mapper in self.effect:
            mapper.activate()


class Map:

    def __init__(self, resource, state):
        self.resource = resource
        self.state = state

    def activate(self):
        if isinstance(self.resource, syrabond.facility.Switch):
            self.resource.turn(self.state)
        elif isinstance(self.resource, syrabond.facility.VirtualAppliance):
            self.resource.set_state(self.state)


class Conditions:

    def __init__(self, id, resource, positive, compare, state):
        self.id = id
        self.resource = resource
        self.positive = positive
        self.compare = compare
        self.state = state

    def check(self):  # TODO Divide for types of resources, make <> work
        if self.compare == '=':
            if self.resource.state == self.state:
                if self.positive:
                    return True
                else:
                    return False
            else:
                if self.positive:
                    return False
                else:
                    return True
        elif self.compare == '>':
            if self.resource.state > self.state:
                if self.positive:
                    return True
                else:
                    return False
        elif self.compare == '<':
            if self.resource.state > self.state:
                if self.positive:
                    return True
                else:
                    return False