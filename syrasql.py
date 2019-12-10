import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, JSON, String, Boolean
from sqlalchemy.orm import sessionmaker
import json
from syrabond import facility

sh = facility.Facility('sh', listen=False)


Base = declarative_base()

class Resource(Base):
    __tablename__ = 'resources'
    uid = Column(String(20), primary_key=True)
    group = Column(String(20))
    hrn = Column(String(40))
    channels = Column(JSON)
    pir = Column(Boolean)

    def __repr__(self):
        return "<Resource(uid='{}', group='{}', hrn='{}'), channels='{}', pir='{}'>".format(self.uid, self.group, self.hrn,
                                                                                        self.channels, self.pir)


engine = sql.create_engine('mysql+pymysql://pythoner:kal1966@192.168.88.12/smarthouse')
Session = sessionmaker(bind=engine)
connection = engine.connect()
session = Session()
Base.metadata.create_all(engine)
db_mirror = {}
[db_mirror.update({res.uid: Resource(uid=res.uid, group=res.group, hrn=res.hrn, channels=res.channels, pir=res.pir)})
 for res in sh.resources.values() if isinstance(res, facility.Device)]
session.add_all(list(db_mirror.values()))
session.commit()
print(db_mirror)
connection.close()
