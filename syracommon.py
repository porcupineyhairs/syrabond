import json
from datetime import datetime
import logging
from os import chdir


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
        f = open(confs_dir+'/'+file_name, 'r')
        items = json.loads(f.read())
        f.close()
    except Exception as e:
        print(e)
        return False
    return items


logging_levels = {
    'CRITICAL': 50,
    'ERROR': 40,
    'WARNING': 30,
    'INFO': 20,
    'DEBUG': 10
}
conf = extract_config('global.json')
chdir(conf['working_dir'])
log_file = '{}/{}'.format(conf['working_dir'], conf['log_file'])
confs_dir = conf['confs_dir']
logging.basicConfig(filename=log_file, level=logging_levels[conf['log_level']])
conf = None
