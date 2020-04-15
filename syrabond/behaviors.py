import threading
from datetime import datetime, timedelta


def invent(resource):
    t = None

    WORKING_TIME = 10
    STANDBY_TIME = 20

    if hasattr(resource, 'timer'):
        print(resource.timer)
        if resource.timer.get('finish_time') > datetime.now():
            resource.timer.get('timer_thread', threading.Timer(1, lambda: print(1))).cancel()
            print('CANCELED!!!')
            delattr(resource, 'timer')
            return

    if resource.state == 'ON':
        t = threading.Timer(WORKING_TIME*60, resource.off)
        setattr(resource, 'timer', {
            'finish_time': datetime.now()+timedelta(minutes=WORKING_TIME),
            'timer_thread': t
        })
    if resource.state == 'OFF':
        t = threading.Timer(STANDBY_TIME*60, resource.on)
        setattr(resource, 'timer', {
            'finish_time': datetime.now()+timedelta(minutes=STANDBY_TIME),
            'timer_thread': t
        })
    if t:
        t.start()
