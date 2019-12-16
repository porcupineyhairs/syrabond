import syrabond.facility


class StateEngine:
    def __init__(self):
        self.resources = {}


class Scenario:  # TODO Add comparison rules for conditions

    def __init__(self, hrn: str, conditions, effect):
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


class Conditions:

    def __init__(self, resource, positive, compare, state):
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