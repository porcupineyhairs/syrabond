import sqlalchemy as sql

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, Column, String, Boolean, ForeignKey, CHAR
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
        self.engine.connect()
        Base.metadata.create_all(self.engine)

    def load_resources(self):
        session = self.Session()
        result = []
        for res in session.query(Resource):
            result.append(res)
        session.close()
        return result

    def load_scenarios(self, type):
        session = self.Session()
        result = []
        for scen in session.query(Scenario).filter_by(type=type):
            result.append({'id': scen.id, 'type': scen.type, 'active': scen.active,
                           'hrn': scen.hrn, 'conditions': scen.conditions,
                           'schedule': scen.schedule, 'effect': scen.effect})
        session.close()
        return result

    def rewrite_resources(self, resources: dict):  # TODO Check is it needed to truncate table first
        session = self.Session()
        session.begin()
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
        session.commit()
        session.close()

    def update_state(self, uid, state):
        session = self.Session()
        if session.query(State).filter_by(resource=uid).first():
            session.query(State).filter_by(resource=uid).update({'state': state})
        else:
            res = session.query(Resource).filter_by(uid=uid).first()
            res.state = [State(state=state)]
        session.query(State).filter_by(resource=None).delete(synchronize_session='fetch')
        #res.state = [State(state=state)]
        session.commit()
        session.close()

    def get_state(self, uid):
        session = self.Session()
        res = session.query(Resource).filter_by(uid=uid).first()
        if res.state:
            result = res.state[0].state
            session.close()
            return result
        else:
            session.close()
            return []

    def update_status(self, uid, status):
        session = self.Session()
        res = session.query(Resource).filter_by(uid=uid).first()
        res.status = [Status(status=status)]
        session.query(Status).filter_by(resource=None).delete(synchronize_session='fetch')
        session.commit()
        session.close()

    def update_tags(self, uid, tags):
        session = self.Session()
        res = session.query(Resource).filter_by(uid=uid).first()
        res.tags = [Tags(tag=tag) for tag in tags]
        session.query(Tags).filter_by(resource=None).delete(synchronize_session='fetch')
        session.commit()
        session.close()

    def update_scenario(self, id, mod):
        session = self.Session()
        scen = session.query(Scenario).filter_by(id=id).first()
        if mod['type'] == 'act':
            scen.active = mod['active']
        session.commit()
        session.close()

    def get_tags(self, uid):
        session = self.Session()
        res = session.query(Resource).filter_by(uid=uid).first()
        if res.tags:
            return [tag.tag for tag in res.tags]
        else:
            return []

    def update_resource_properties(self, entity):
        session = self.Session()
        res = session.query(Resource).filter_by(uid=entity.uid).first()
        res.type = entity.type
        res.hrn = entity.hrn
        res.group = entity.group
        res.channels = ''
        if entity.channels:
            res.channels = ', '.join(entity.channels)
        session.commit()
        session.close()
        self.update_tags(entity.uid, entity.tags)

    def get_entropy(self):
        session = self.Session()
        entity = session.query(Entropy).filter_by(id=1).first()
        if entity:
            return entity.entropy
        else:
            return 0

    def truncate_entropy(self):
        session = self.Session()
        session.query(Entropy).delete()
        session.commit()
        session.close()

    def increase_entropy(self):
        session = self.Session()
        entity = session.query(Entropy).filter_by(id=1).first()
        if entity:
            entity.entropy += 1
        else:
            session.add(Entropy(id=1,
                                entropy=0))
        session.commit()
        session.close()

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
    state = relationship("State")
    status = relationship("Status")
    tags = relationship("Tags")

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


class Tags(Base):
    """Table containing tags."""
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True)
    tag = Column(String(40))
    resource = Column(String(40), ForeignKey('resources.uid'))

    def __repr__(self):
        return "<Tags(tag='{}'>".format(self.tag)


class Entropy(Base):
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

    def __repr__(self):
        return "<Schedule(id='{}')>".format(self.id)
