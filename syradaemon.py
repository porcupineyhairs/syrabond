#!/usr/bin/python3
import signal
from time import sleep
from syrabond import facility, orm, automation

"""Demo daemon that receive and handle messages, check schedules in loop"""


class GracefulKiller:

    def __init__(self):
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        print(f'Shutdown signal has arrived: {signum}')
        self.kill_now = True


def scheduler():
    scheduler.i += 1
    if scheduler.i > 25:
        te.load_scenarios()
        sh.build_scenarios()
        scheduler.i = 0
    scens = te.check_schedule()
    if scens:
        [scen.workout() for scen in scens]


blocking = True

sh = facility.Facility('sh', listen=True, addons=['homekit'])
orm = orm.DBO('mysql')
te = automation.TimeEngine(sh, orm)

killer = GracefulKiller()

scheduler.i = 0
if blocking:
    i = 31
    while not killer.kill_now:
        if i > 30:
            scheduler()
            i = 0
        sh.listener.check_for_messages()
        sh.message_handler()
        i += 1
        sleep(0.1)

    sh.shutdown()

else:
    sh.listener.wait_for_messages()





