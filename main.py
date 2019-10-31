#!/usr/bin/python3
import syrabond
from time import sleep


sh = syrabond.API('sh', listen=True)
i = 20
while i > 0:
    sh.facility.listener.check_for_messages()
    sleep(0.1)
    i -= 1
sh.facility.message_handler()
sh.facility.listener.disconnect()
print('Список переключателей:')
i = 0
switches = {}
for r in sh.facility.resources:
    res = sh.facility.resources[r]
    if res.type == 'switch':
        i += 1
        print('{}) {} ({})'.format(i, res.hrn, res.uid))
        switches.update({i: res})
while True:
    choice = input('Индекс (#) или API (A)? ')
    try:
        choice = int(choice)
        if choice in switches:
            com = input('on (1) | off (0) | reboot (r) | webrepl (w)')
            r = switches[int(choice)]
            if com == '1':
                r.on()
            elif com == '0':
                r.off()
            elif com == 'r':
                r.device_reboot()
            elif com == 'w':
                r.webrepl('on')
            else:
                break
            sleep(0.5)
    except ValueError:
        if choice == 'A':
            base = input('Укажите API-строку')
            sh.parse_n_direct(tuple(base))
        else:
            break
    finally:
        print('Список переключателей:')
        i = 0
        switches = {}
        for r in sh.facility.resources:
            res = sh.facility.resources[r]
            if res.type == 'switch':
                i += 1
                print('{}) {} ({})'.format(i, res.hrn, res.uid))
                switches.update({i: res})
