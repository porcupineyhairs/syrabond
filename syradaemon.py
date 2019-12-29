#!/usr/bin/python3
from os import chdir
from time import sleep
from syrabond import facility, orm, automation

"""Demo daemon that receive and handle messages, check schedules in loop"""

blocking = True

#chdir('/home/pi/syrabond/python')
#chdir('/Users/egor/PycharmProjects/syrabond/')
sh = facility.Facility('sh', listen=True)
orm = orm.DBO('mysql')
te = automation.TimeEngine(sh, orm)


def scheduler():
    scens = te.check_shedule()
    if scens:
        [scen.workout() for scen in scens]


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





