#!/usr/bin/python3
## This script uses Syrabond to activate scenes

import syrabond
import json
import sys
from pathlib import Path
from syrabond2.main_app.common import extract_config

KEYWORDS = {
    'device': 'shift_device',
    'group': 'shift_group',
    'premise': 'shift_prem_property'
}


def parse(command_string):
    keyword = command_string.split(' ')[0]
    params = command_string.replace(keyword, '').strip()
    return [keyword, params]


def direct(instruction, arg):
    print(instruction, arg)
    method = KEYWORDS[instruction[0]]
    getattr(api, method)(instruction[1], arg)


def scenary(filename):
        try:
            f = open(filename, 'r')
        except IOError:
            sys.exit('Unable to open the file.')
        items = json.loads(f.read())
        f.close()
        for key, value in items.items():
                    print('{} --- {}'.format(key, value))
                    if key.split(' ')[0] in KEYWORDS:
                        direct(parse(key), value)
                    else:
                        direct(['device', key], value)
        return True


if __name__ == "__main__":
    try:
        param = sys.argv[1]
    except IndexError:
        sys.exit('Error: don\'t specified scenario file name!')
    my_file = Path(param)
    if not my_file.is_file():
        sys.exit('Error: file {} does not exist'.format(my_file))
    else:
        config = extract_config('global.json')
        facility_name = config['facility_name']
        config = None
        api = syrabond.API(facility_name)
        print(scenary(param))

