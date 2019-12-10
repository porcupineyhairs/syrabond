#!/usr/bin/python3
from os import chdir
from time import sleep
from syrabond import facility

blocking = True

chdir('/home/pi/syrabond/python')
sh = facility.Facility('sh')

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





