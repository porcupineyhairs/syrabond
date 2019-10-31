import serial
from curses import ascii
from time import sleep
import sys


def get_level():
    ser = serial.Serial('/dev/ttyS0', 9600, timeout=2)
    print (ser.name)
    ser.write("AT\n".encode())
    ser.write("AT+CSQ\n".encode())
    ser.write(ascii.ctrl('z').encode())
    print (ser.readline())
    print (ser.readline())
    print (ser.readline())
    ser.close()
    return


def sendsms(phone_number, text):
    ser = serial.Serial('/dev/ttyS0', 9600, timeout=1)
    print (ser.name)

    ser.write("AT\n".encode())
    ser.write("AT+CMGF=1\n".encode())
    ser.write(('AT+CMGS="%s"\n' % phone_number).encode())
    sleep(1)
    ser.write(text.encode())
    sleep(1)
    ser.write(ascii.ctrl('z').encode())
    sleep(1)
    print (ser.readline())
    print (ser.readline())
    print (ser.readline())

    ser.close()
    return


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print ("Wrong number of arguments")
        print ("Usage: sendsms.py <phone number> <message text>")
        sys.exit(-1)
    phone_number = sys.argv[1]
    sms = sys.argv[2]
    #get_level()
    sendsms(phone_number, sms)
