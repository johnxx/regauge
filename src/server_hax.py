from io import BytesIO 
import msgpack
import socketpool
import sys
import wifi
import gc

print("Freemem: %s" % gc.mem_free())
ssid = "Pequod"
key = "Call me Ishy."
print("Connecting to " + ssid)
wifi.radio.connect(ssid, key)
print("Connected! IP: {}".format(wifi.radio.ipv4_address))
sp = socketpool.SocketPool(wifi.radio)

# Bind a pool for MsgPack
pool_mp = sp.socket(sp.AF_INET, sp.SOCK_STREAM)
pool_mp.bind(("0.0.0.0", 7777))
pool_mp.listen(2)
pool_mp.setblocking(False)

# Bind a pool for HTTP
pool_http = sp.socket(sp.AF_INET, sp.SOCK_STREAM)
pool_http.bind(("0.0.0.0", 80))
pool_http.listen(2)
pool_http.setblocking(False)


class Listener:
    def __init__(self, pool):
        self._pool = pool

    def listen(self):
        try:
            connected_sock, remote_addr = self._pool.accept()
            with connected_sock:
                data = self.receive(connected_sock)
                self.handle(data)
        except OSError as e:
            if e.errno == 11:
                pass
            else:
                print(e)


class MPHandler(Listener):
    @staticmethod
    def receive(connected_sock):
        data = b''
        recv_buffer = bytearray(8)
        while True:
            try:
                count = connected_sock.recv_into(recv_buffer)
                if count == 0:
                    break
                data += recv_buffer[:count]
            except OSError as e:
                if e.errno == 11 and len(data) == 0:  # Nothing Received
                    pass
                elif e.errno == 11:  # Finished Sending
                    break
                else:
                    print(e)
        return data

    @staticmethod
    def handle(data):
        print("processing msgpack data")
        res = msgpack.unpack(BytesIO(data))
        print(res)

class HTTPHandler(Listener):
    METHOD = 1
    PATH = 2
    VERSION = 3
    HEADERS = 4
    DATA = 5

    @classmethod
    def handle(cls, data):
        print("processing http data")
        path = data[cls.PATH]
        data = msgpack.unpack(BytesIO(data[cls.DATA]))
        getattr(cls, 'handle_%s' % path[1:])(data)

    @staticmethod
    def handle_(data):
        print(data)
        print("Freemem: %s" % gc.mem_free())

    @classmethod
    def receive(cls, connected_sock):
        data = {
            cls.METHOD: '',
            cls.PATH: '',
            cls.VERSION: '',
            cls.HEADERS: {},
            cls.DATA: b''
        }
        recv_buffer = bytearray(1)
        current = cls.METHOD
        last = b''
        skip = False
        current_header_key = ''
        current_header_value = ''
        header_mode_key = True
        while True:
            try:
                count = connected_sock.recv_into(recv_buffer)
                if count == 0:
                    break
                if skip:
                    skip = False
                    continue
    
                if current == cls.METHOD and recv_buffer == b' ':
                    current = cls.PATH
                elif current == cls.PATH and recv_buffer == b' ':
                    current = cls.VERSION
                elif current == cls.VERSION and recv_buffer == b'\r':
                    current = cls.HEADERS
                    skip = True
                elif current == cls.HEADERS and last == b'\r\n\r\n':
                    current = cls.DATA
                    last = None
                    data[cls.DATA] += recv_buffer
                    recv_buffer = bytearray(256)
                elif current == cls.HEADERS and recv_buffer == b'\r':
                    if len(current_header_value) > 0:
                        data[cls.HEADERS][current_header_key] = current_header_value
                        current_header_key = ''
                        current_header_value = ''
                        header_mode_key = True
                    last += b'\r'
                elif current == cls.HEADERS and recv_buffer == b'\n':
                    last += b'\n'
                elif current == cls.HEADERS:
                    last = b''
                    continue
                    if recv_buffer == b':':
                        header_mode_key = False
                    elif header_mode_key:
                        current_header_key += recv_buffer.decode()
                    else:
                        if len(current_header_value) == 0 and recv_buffer == b' ':
                            continue
                        current_header_value += recv_buffer.decode()
                elif current == cls.DATA:
                    data[current] += recv_buffer[:count]
                else:
                    data[current] += recv_buffer[:count].decode()
            except OSError as e:
                if e.errno == 11 and len(data[cls.METHOD]) == 0:
                    pass
                elif e.errno == 11:
                    connected_sock.send("%s 200 OK" % data[cls.VERSION])
                    break
                else:
                    print(e)
        return data

print("Freemem: %s" % gc.mem_free())

mp_handler = MPHandler(pool_mp)
http_handler = HTTPHandler(pool_http)

print("Listening...")
while True:
    print("Freemem: %s" % gc.mem_free())
    try:
        mp_handler.listen()
        http_handler.listen()
        # do_next_thing()
        # do_next_thing()
        # do_next_thing()
    except OSError as e:
        print(e)
