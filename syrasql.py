import sqlalchemy as sql


engine = sql.create_engine('mysql+pymysql://pythoner:kal1966@192.168.88.12/smarthouse')
connection = engine.connect()
result = connection.execute("select uid, status from Dev_status where status = 'offline'")
for row in result:
    print("Offile:", row['uid'])
connection.close()
