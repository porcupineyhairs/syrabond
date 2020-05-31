from time import sleep

from syrabond2.main_app.mqttsender import Mqtt

from syrabond2.handler import MessageHandler
from syrabond2.settings import RQ_NAME

if __name__ == '__main__':

    worker = MessageHandler()

    while True:
        worker.listener.check_for_messages()
        sleep(1)
