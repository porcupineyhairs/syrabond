#!/usr/bin/python3
from os import chdir
from time import sleep
from syrabond import facility

"""Demo daemon that receive and handle messages in loop"""

blocking = True

#chdir('/home/pi/syrabond/python')
chdir('/Users/egor/PycharmProjects/syrabond/')
sh = facility.Facility('sh', listen=True)

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





