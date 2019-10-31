import json
from datetime import datetime
import logging
from os import chdir

chdir('/etc/openhab2/python')
logfile = '/etc/openhab2/python/listener.log'
logging.basicConfig(filename=logfile, level=logging.INFO)


def log(line, log_type='info'):
    time_string = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    print(time_string, line)
    if log_type == 'info':
        logging.info(' {} {}'.format(time_string, line))
    if log_type == 'error':
        logging.error(' {} {}'.format(time_string, line))


def extract_config(file_name):
    # type: (str) -> dict
    """
Opening file <param> and extracting json to dict.
    :rtype: dict
    :param file_name: path to config file
    """
    try:
        f = open(file_name, 'r')
        items = json.loads(f.read())
        f.close()
    except Exception as e:
        print(e)
        return False
    return items
