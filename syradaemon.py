#!/usr/bin/python3
from time import sleep
from syrabond import facility, orm, automation

"""Demo daemon that receive and handle messages, check schedules in loop"""

blocking = True

sh = facility.Facility('sh', listen=True)
orm = orm.DBO('mysql')
te = automation.TimeEngine(sh, orm)


def scheduler():
    scheduler.i += 1
    if scheduler.i > 50:
        te.load_scenarios()
        scheduler.i = 0
    scens = te.check_schedule()
    if scens:
        [scen.workout() for scen in scens]


scheduler.i = 0
if blocking:
    i = 31
    while True:
        if i > 30:
            scheduler()
            i = 0
        sh.listener.check_for_messages()
        sh.message_handler()
        i += 1
        sleep(0.1)
else:
    sh.listener.wait_for_messages()





