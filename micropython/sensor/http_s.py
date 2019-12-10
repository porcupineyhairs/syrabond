from machine import Pin
import machine
import usocket
import network
from time import sleep
import ujson as json

led = Pin(13, Pin.OUT)

def form_page(socket, iter):
    socket.send("HTTP/1.1 OK\r\n")
    socket.send("Content - Type: text / html\r\n\r\n")
    socket.send("""<!DOCTYPE HTML>
    <html style='font-family: courier; color: white'>
     <head>
      <meta charset='utf-8'>
      <title>Настройка Wi-Fi</title>
     </head><body bgcolor='blue'>
     """)
    if iter:
        socket.send(
            "<center><h3 style='color: red'>Не удалось подключиться используя введенные данные. Can not connect using this data.</h3></center>")
        socket.send(
            "<center><h3>Пожалуйста, проверьте настройки и заполните форму снова. Please, fill the form correct.:</h3></center>")
    else:
        socket.send("<center><h3>Пожалуйста, заполните форму и укажите настройки. Please, fill the form:</h3></center>")
    socket.send("<br>")
    socket.send("<form name='wifi' method='post' action='/'>")
    socket.send("<p><b>SSID (имя сети):</b><br>")
    socket.send("<input type='text' name='ssid' size='40' required></p>")
    socket.send("<p><b>Password (пароль):</b><br>")
    socket.send("<input type='text' name='pass' size='40' required></p><br>")
    socket.send("<p><input type='submit' value='Отправить'><input type='reset' value='Очистить'></p>")
    socket.send("</form></body></html>")


def try_to_connect(wifi):
    print('Trying to connect to '+wifi[0] + ' with '+wifi[1])
    led.value(0)
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        sta_if.active(True)
        sta_if.connect(wifi[0], wifi[1])
        t = 0
        while not sta_if.isconnected():
            if t < 15:
                led.value(0)
                sleep(0.5)
                led.value(1)
                sleep(0.5)
                t += 1
                pass
            else:
                print('Wrong credentials')
                led.value(0)
                return (False)
    print('Connected: ', sta_if.ifconfig())
    led.value(1)
    return True


def save_creds(wifi):
    dict = {}
    dict['ssid'] = wifi[0]
    dict['pass'] = wifi[1]
    encoded = json.dumps(dict)
    try:
        f = open('network.json', 'w')
        f.write('')
        f.close()
        f = open('network.json', 'w')
        f.write(encoded)
        f.close()
    except:
        print('Could not write config file')



def err(socket, code, message):
    socket.send("HTTP/1.1 "+code+" "+message+"\r\n\r\n")
    socket.send("<h1>"+message+"</h1>")

def handle(socket):
    (method, url, version) = socket.readline().split(b" ")
    if b"?" in url:
        (path, query) = url.split(b"?", 2)
    else:
        (path, query) = (url, b"")
    # while True:
    #     header = socket.readline()
    #     print(header)
    #     if header == b"":
    #         return
    #     if header == b"\r\n":
    #         break
    if version != b"HTTP/1.0\r\n" and version != b"HTTP/1.1\r\n":
        err(socket, "505", "Version Not Supported")
    elif method == b"GET":
        if path == b"/":
            while True:
                header = socket.readline()
                if header == b"":
                    return
                if header == b"\r\n":
                    break
            form_page(socket, 0)
        elif path == b"/again":
            while True:
                header = socket.readline()
                if header == b"":
                    return
                if header == b"\r\n":
                    break
            form_page(socket, 1)
        else:
            err(socket, "404", "Not Found")
    elif method == b"POST":
        if path == b"/":
            while True:
                h = socket.readline()
                if h == b"\r\n":
                    break
            data = socket.readline()
            print(data)
            (ssid, passwd) = data.decode().split('&')
            ssid = ssid.replace('ssid=','')
            passwd = passwd.replace('pass=','')
            print(ssid, passwd)
            return ssid, passwd
        else:
            err(socket, "404", "Not Found")
    else:
        err(socket, "501", "Not Implemented")

print('Starting web server')
server = usocket.socket()
server.bind(('0.0.0.0', 80))
server.listen(5)
i = 10
while i:
    i -= 1
    try:
        socket, sockaddr = server.accept()
        wifi = handle(socket)
        if wifi:
            luck = try_to_connect(wifi)
            if luck:
                save_creds(wifi)
                machine.reset()

            else:
                print('else')
                form_page(socket, 1)

    except:
        socket.send("HTTP/1.1 500 Internal Server Error\r\n\r\n")
        socket.send("<h1>Internal Server Error</h1>")
    socket.close()
