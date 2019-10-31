#!/usr/bin/python3
import syrabond
from time import sleep

blocking = True

sh = syrabond.Facility('sh')

if blocking:
    while True:
        sh.listener.check_for_messages()
        sh.message_handler()
        sleep(0.1)
        """
        Timechecker for unlimited jsons with
        time: action
        """
else:
    sh.listener.wait_for_messages()





