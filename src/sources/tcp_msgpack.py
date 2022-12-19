from io import BytesIO
from tcp_server import ListenServer
import json
import msgpack

debug = True
def print_dbg(some_string, **kwargs):
    if debug:
        return print(some_string, **kwargs)

class DataSource(ListenServer):
    def __init__(self, name, resources, target, bind_addr="0.0.0.0", listen_port=5189, listeners=5, poll_freq=30, enabled=True) -> None:
        super().__init__(name, resources, target, bind_addr, listen_port, listeners)
        self.data_bus = resources['data_bus']
        
    def handle(self, payload):
        try:
            res = msgpack.unpack(BytesIO(payload))
        except Exception as e:
            return False
        for key, value in res.items():
            if key not in self.target:
                self.target[key] = {}
            if 'value' not in self.target[key] or self.target[key]['value'] != value:
                print_dbg("Set {} to {}".format(key, value))
                self.target[key]['value'] = value
                msg_topic = "data.{}".format(key)
                self.data_bus.pub(msg_topic, value, auto_send=False)
        self.data_bus.send_all()

    def receive(self, connected_sock):
        recv_buffer = bytearray(8)
        payload = b''
        while True:
            try:
                count = connected_sock.recv_into(recv_buffer)
                if count == 0:
                    break
                print_dbg("Read {} bytes".format(count))
                payload += recv_buffer[:count]
            except OSError as e:
                if e.errno == 11:
                    if len(payload) == 0: # Nothing received
                        # print_dbg("Got nothing")
                        pass
                    else: # Finished sending
                        # print_dbg("Done receiving")
                        break
                else:
                    print(e)
        return payload