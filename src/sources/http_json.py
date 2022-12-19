from io import BytesIO
from tcp_server import ListenServer
import json

debug = True
def print_dbg(some_string, **kwargs):
    if debug:
        return print(some_string, **kwargs)

def merge(a, b, path=None, notifier=None):
    "merges b into a"
    if path is None: path = []
    for key in b:
        topic = "config." + ".".join(path + [key])
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)], notifier)
            elif a[key] == b[key]:
                pass # same leaf value
            else:
                a[key] = b[key]
                if notifier:
                    notifier(topic, a[key])
        else:
            a[key] = b[key]
            if notifier:
                notifier(topic, a[key])
    return a

class ConfigSource(ListenServer):
    METHOD = 1
    PATH = 2
    VERSION = 3
    HEADERS = 4
    DATA = 5

    def __init__(self, name, resources, target, bind_addr="0.0.0.0", listen_port=80, listeners=5, poll_freq=5, enabled=True) -> None:
        self.msgbus = resources['config_bus']
        super().__init__(name, resources, target, bind_addr, listen_port, listeners)
        
    def handle(self, payload):
        path = payload[self.PATH]
        method = payload[self.METHOD].lower()
        headers = payload[self.HEADERS]
        try:
            res = json.loads(payload[self.DATA])
        except Exception as e:
            return False
        # print(payload)
        getattr(self, 'handle_{}_{}'.format(method, path[1:]))(headers, res)
        
    def handle_post_config(self, headers, data):
        merge(self.target, data, notifier=self.msgbus.pub)

    def receive(self, connected_sock):
        payload = {
            self.METHOD: '',
            self.PATH: '',
            self.VERSION: '',
            self.HEADERS: {},
            self.DATA: b''
        }
        recv_buffer = bytearray(1)
        current = self.METHOD
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
    
                if current == self.METHOD and recv_buffer == b' ':
                    current = self.PATH
                elif current == self.PATH and recv_buffer == b' ':
                    current = self.VERSION
                elif current == self.VERSION and recv_buffer == b'\r':
                    current = self.HEADERS
                    skip = True
                elif current == self.HEADERS and last == b'\r\n\r\n':
                    current = self.DATA
                    last = None
                    payload[self.DATA] += recv_buffer
                    recv_buffer = bytearray(256)
                elif current == self.HEADERS and recv_buffer == b'\r':
                    if len(current_header_value) > 0:
                        payload[self.HEADERS][current_header_key] = current_header_value
                        current_header_key = ''
                        current_header_value = ''
                        header_mode_key = True
                    last += b'\r'
                elif current == self.HEADERS and recv_buffer == b'\n':
                    last += b'\n'
                elif current == self.HEADERS:
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
                elif current == self.DATA:
                    payload[current] += recv_buffer[:count]
                else:
                    payload[current] += recv_buffer[:count].decode()
            except OSError as e:
                if e.errno == 11 and len(payload[self.METHOD]) == 0:
                    pass
                elif e.errno == 11:
                    connected_sock.send("%s 200 OK" % payload[self.VERSION])
                    break
                else:
                    print(e)
        return payload
