import sqlalchemy as sql

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, Column, String, Boolean, ForeignKey, CHAR, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship

from syrabond import common

Base = declarative_base()


class DBO:

    def __init__(self, sql_engine: str):
        config = common.extract_config(sql_engine+'.json')
        self.engine = sql.create_engine('mysql+pymysql://{}:{}@{}/{}?charset=utf8'.format(  # TODO Make dependence to sql_engine
                                        config['user'], config['password'], config['host'], config['database']),
                                        pool_pre_ping=True)
        self.Session = sessionmaker(bind=self.engine)
        self.connection = self.engine.connect()
        self.log = common.log
        Base.metadata.create_all(self.engine)

    def _session_maker(f):
        """
        Wrapper for every DB function. Build session and pass it into the function, securely commit and close sessions.
        To check if function needs commit, it must return tuple with True or False on position zero.
        On the first position expected result of query etc.
        """
        def wrap(self, *args):
                s = self.Session()
                res = f(self, s, *args)
                if res[0]:
                    try:
                        s.commit()
                    except Exception as e:
                        s.rollback()
                        self.log(f'DB error: {e}')
                    finally:
                        s.close()
                else:
                    s.close()
                return res[1]
        return wrap

    @_session_maker
    def load_resources(self, session):
        result = []
        for res in session.query(Resource):
            result.append(res)
        return False, result

    @_session_maker
    def load_scenarios(self, session, type):
        result = []
        for scen in session.query(Scenario).filter_by(type=type):
            result.append({'id': scen.id, 'type': scen.type, 'active': scen.active,
                           'hrn': scen.hrn, 'conditions': scen.conditions,
                           'schedule': scen.schedule, 'effect': scen.effect})
        return False, result

    @_session_maker
    def load_quarantine(self, session):
        result = []
        for res in session.query(Quarantine):
            result.append({'uid': res.resource, 'ip': res.status})
        return False, result

    @_session_maker
    def put_quarantine(self, session, uid, ip):
        res = session.query(Quarantine).filter_by(resource=uid).first()
        if res:
            res.status = ip
            return True, None
        else:
            session.add(Quarantine(resource=uid, status=ip))
            return True, None

    @_session_maker
    def un_quarantine(self, session, uid):
        res = session.query(Quarantine).filter_by(resource=uid).first()
        print(f'Uncar {res}')
        session.delete(res)
        return True, None

    @_session_maker
    def rewrite_resources(self, session, resources: dict):  # TODO Check is it needed to truncate table first
        res_list = []
        resources_copy = resources.copy()
        for res in resources_copy.values():
            channels = pir = None
            if res.type == 'switch' or res.type == 'sensor':
                if res.channels:
                    channels = ','.join(res.channels)
                if res.pir:
                    pir = res.pir
            res_list.append(Resource(uid=res.uid, type=res.type, group=res.group, hrn=res.hrn, channels=channels, pir=pir))
        session.add_all(res_list)
        return True, None

    @_session_maker
    def update_state(self, session, uid, state):
        if session.query(State).filter_by(resource=uid).first():
            session.query(State).filter_by(resource=uid).update({'state': state})
        else:
            res = session.query(Resource).filter_by(uid=uid).first()
            res.state = [State(state=state)]
        session.query(State).filter_by(resource=None).delete(synchronize_session='fetch')
        return True, None

    @_session_maker
    def get_state(self, session, uid):
        res = session.query(Resource).filter_by(uid=uid).first()
        if res and res.state:
            result = res.state[0].state
            return False, result
        else:
            return False, []

    @_session_maker
    def get_status(self, session, uid):
        res = session.query(Resource).filter_by(uid=uid).first()
        if res.status:
            result = res.status[0].status
            return False, result
        else:
            return False, []

    @_session_maker
    def update_status(self, session, uid, status):
        res = session.query(Resource).filter_by(uid=uid).first()
        if res:
            res.status = [Status(status=status)]
            session.query(Status).filter_by(resource=None).delete(synchronize_session='fetch')
            return True, None
        else:
            self.log(f'DBO: Object {uid} doesn\'t exist', 'warning')
            return False, None

    @_session_maker
    def update_tags(self, session, uid, tags):
        res = session.query(Resource).filter_by(uid=uid).first()
        res.tags = [Tags(tag=tag) for tag in tags]
        session.query(Tags).filter_by(resource=None).delete(synchronize_session='fetch')
        return True, None

    @_session_maker
    def update_scenario(self, session, id, mod):
        result = None
        scen = session.query(Scenario).filter_by(id=id).first()
        if mod['type'] == 'act':
            scen.active = mod['active']
        if mod['type'] == 'time':
            for schedule in scen.schedule:
                if schedule.id == int(mod['schedule']):
                    schedule.start = mod['time'].replace(':', ',')
        if mod['type'] == 'weekday':
            schedule = None
            for sch in scen.schedule:
                if sch.id == int(mod['schedule']):
                    schedule = sch
            if schedule:
                weekdays = schedule.weekdays.split(',')
                if weekdays and mod['weekday']:
                    if weekdays.count(''):
                        weekdays.remove('')
                    if mod['active']:
                        weekdays.append(mod['weekday'])
                    else:
                        weekdays.remove(mod['weekday'])
                    schedule.weekdays = ','.join(weekdays)
        if mod['type'] == 'schedule':
            if mod['schedule'].isdigit():
                for sch in scen.schedule:
                    if sch.id == int(mod['schedule']):
                        session.delete(sch)
            elif mod['schedule'] == 'new':
                new_schedule = Schedule(weekdays='', start='00,00')
                scen.schedule.append(new_schedule)
                session.commit()
                result = new_schedule.id

        return True, result

    @_session_maker
    def get_tags(self, session, uid):
        res = session.query(Resource).filter_by(uid=uid).first()
        if res.tags:
            return False, [tag.tag for tag in res.tags]
        else:
            return False, []

    @_session_maker
    def update_resource_properties(self, session, entity):
        res = session.query(Resource).filter_by(uid=entity.uid).first()
        if res:
            res.type = entity.type
            res.hrn = entity.hrn
            res.group = entity.group
            res.channels = ''
            if entity.channels:
                res.channels = ', '.join(entity.channels)
            self.update_tags(entity.uid, entity.tags)
        else:
            self.build_new_resource(entity)
        return True, None

    @_session_maker
    def build_new_resource(self, session, entity):
        res = Resource(uid=entity.uid, type=entity.type, group=entity.group, hrn=entity.hrn,
                       channels=entity.channels, pir=entity.pir)
        session.add(res)
        return True, None

    @_session_maker
    def delete_resource(self, session, uid):
        # TODO It's necessary to iterate through the linked tables and delete all.
        res = session.query(Resource).filter_by(uid=uid).first()
        session.delete(res)
        return True, None


class Resource(Base):
    """
    Table for resources list with uid primary key.
    The base table for one-to-many relations.
    """
    __tablename__ = 'resources'
    uid = Column(String(40), primary_key=True)
    type = Column(String(10))
    group = Column(String(20))
    hrn = Column(String(40))
    channels = Column(String(20))
    pir = Column(Boolean)
    plugin = Column(String(20))
    state = relationship("State")
    status = relationship("Status")
    tags = relationship("Tags")
    behavior = relationship("Behaviors", lazy="joined")

    def __repr__(self):
        return "<Resource(uid='{}'>".format(self.uid)


class State(Base):
    """Table for resources current states."""
    __tablename__ = 'states'
    id = Column(Integer, primary_key=True)
    resource = Column(String(40), ForeignKey('resources.uid'))
    state = Column(String(40))

    def __repr__(self):
        return "<State(state='{}'>".format(self.state)


class Status(Base):
    """Table for resources current states."""
    __tablename__ = 'statuses'
    id = Column(Integer, primary_key=True)
    resource = Column(String(40), ForeignKey('resources.uid'))
    status = Column(String(40))

    def __repr__(self):
        return "<Status(status='{}'>".format(self.status)


class Quarantine(Base):
    """Table for newbies or quarantined resources"""
    __tablename__ = 'quarantine'
    id = Column(Integer, primary_key=True)
    resource = Column(String(40))
    status = Column(String(40))

    def __repr__(self):
        return "<Quarantine(resource='{}'>".format(self.resource)


class Tags(Base):
    """Table containing tags."""
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True)
    tag = Column(String(40))
    resource = Column(String(40), ForeignKey('resources.uid'))

    def __repr__(self):
        return "<Tags(tag='{}'>".format(self.tag)


class Entropy(Base):  # TODO Delete
    """Table to hold entropy."""
    __tablename__ = 'entropy'
    id = Column(Integer, primary_key=True)
    entropy = Column(Integer)

    def __repr__(self):
        return "<Entropy(entropy='{}'>".format(self.tag)


class Scenario(Base):
    """Table for scernario's conditions."""
    __tablename__ = 'scenarios'
    id = Column(Integer, primary_key=True)
    active = Column(Boolean)
    type = Column(String(10))
    hrn = Column(String(50))
    conditions = relationship("Conditions")
    schedule = relationship("Schedule")
    effect = relationship("Map")

    def __repr__(self):
        return "<Scenario(id='{}')>".format(self.id)


class Map(Base):
    """Table for scernario's conditions."""
    __tablename__ = 'maps'
    id = Column(Integer, primary_key=True)
    resource = Column(String(40), ForeignKey('resources.uid'))
    state = Column(String(40))
    scenario = Column(Integer, ForeignKey('scenarios.id'))

    def __repr__(self):
        return "<Map(id='{}')>".format(self.id)


class Conditions(Base):
    """Table for scernario's conditions."""
    __tablename__ = 'conditions'
    id = Column(Integer, primary_key=True)
    resource = Column(String(40), ForeignKey('resources.uid'))
    positive = Column(Boolean)
    compare = Column(CHAR)
    state = Column(String(40))
    scenario = Column(Integer, ForeignKey('scenarios.id'))

    def __repr__(self):
        return "<Conditions(id='{}')>".format(self.id)


class Schedule(Base):
    """Table for scernario's Schedule."""
    __tablename__ = 'schedule'
    id = Column(Integer, primary_key=True)
    weekdays = Column(String(18))
    start = Column(String(9))
    end = Column(String(9))
    scenario = Column(Integer, ForeignKey('scenarios.id'))


class Behaviors(Base):
    __tablename__ = 'behaviors'
    id = Column(Integer, primary_key=True)
    active = Column(Boolean)
    function = Column(String(40))
    name = Column(String(40))
    params = Column(Text)
    resource = Column(String(40), ForeignKey('resources.uid'))

    def __repr__(self):
        return "<Behavior(id='{}')>".format(self.id)
