import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import sessionmaker
import json

Base = declarative_base()


class DBO:

    def __init__(self):
        self.engine = sql.create_engine('mysql+pymysql://pythoner:kal1966@192.168.88.12/smarthouse')
        self.Session = sessionmaker(bind=self.engine)
        connection = self.engine.connect()
        Base.metadata.create_all(self.engine)

    def load_resources(self):
        session = self.Session()
        result = []
        for res in session.query(Resource):
            result.append(res)
        return result

    def rewrite_resources(self, resources: dict):
        session = self.Session()
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


class Resource(Base):
    __tablename__ = 'resources'
    uid = Column(String(40), primary_key=True)
    type = Column(String(10))
    group = Column(String(20))
    hrn = Column(String(40))
    channels = Column(String(20))
    pir = Column(Boolean)

    def __repr__(self):
        return "<Resource(uid='{}'>".format(self.uid)

