import threading
from datetime import datetime, timedelta


def timed_throwback(resource, params: dict):
    """
    :param resource: facility.Resource
    :param params: dict()
    {
    'working_time': int (minutes)
    'standby_time;: int (minutes)
    }
    :return: None
    """

    t = None

    WORKING_TIME = params.get('working_time')
    STANDBY_TIME = params.get('standby_time')

    if hasattr(resource, 'timer'):

        if resource.timer.get('finish_time') > datetime.now():
            resource.timer.get('timer_thread', threading.Timer(1, lambda: print(1))).cancel()
            print('CANCELED!!!')
            delattr(resource, 'timer')
            return

        if resource.state == 'OFF':
            t = threading.Timer(STANDBY_TIME*60, resource.on)
        setattr(resource, 'timer', {
            'finish_time': datetime.now()+timedelta(minutes=STANDBY_TIME),
            'timer_thread': t
        })

    if resource.state == 'ON':
        t = threading.Timer(WORKING_TIME*60, resource.off)
        setattr(resource, 'timer', {
            'finish_time': datetime.now()+timedelta(minutes=WORKING_TIME),
            'timer_thread': t
        })

    if t:
        t.start()
