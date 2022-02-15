import ampule
import json
import os
from io import BytesIO

debug = True
def print_dbg(some_string, **kwargs):
    if debug:
        return print(some_string, **kwargs)

def serve_file(path_el):
    path = os.sep.join(path_el)
    try:
        with open(path, "r") as f:
            return (200, {}, f.read())
    except OSError as e:
        return (404, {}, "{} not found".format(path))

@ampule.route("/")
def index(request):
    return serve_file(["web", "index.html"])

@ampule.route("/files/<filename>")
def files(request, filename):
    return serve_file(["files", filename])


class ConfigSource():

    def __init__(self, name, resources, target, bind_addr="0.0.0.0", listen_port=80, listeners=5, poll_freq=5) -> None:
        self.msgbus = resources['config_bus']
        self.name = name
        if not bind_addr:
            raise ValueError("Bind address (bind_addr) is required")
        if not listen_port:
            raise ValueError("Listen port (listen_port) is required")

        socket_pool = resources['socket_pool']
        listen_sock = socket_pool.socket(socket_pool.AF_INET, socket_pool.SOCK_STREAM)
        listen_sock.bind((bind_addr, listen_port))
        listen_sock.listen(listeners)
        listen_sock.setblocking(False)
        self.listen_sock = listen_sock
        self.target = target
        self._poll_freq = poll_freq
        
    @property
    def poll_freq(self):
        return self._poll_freq

    async def poll(self):
        ampule.gauge_face = self
        try:
            ampule.listen(self.listen_sock, context=self)
        except Exception as e:
            pass
