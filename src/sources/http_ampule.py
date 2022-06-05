import ampule
import json
import os
import re
from io import BytesIO

debug = False
def print_dbg(some_string, **kwargs):
    if debug:
        return print(some_string, **kwargs)

def merge(a, b, path=None, notifier=None, debug_below=False):
    "merges b into a"
    if path is None: path = []
    print_dbg("Merging: {}".format(json.dumps(path)))
    if debug_below: 
        print(json.dumps(a))
        print(json.dumps(b))
    for key in b:
        topic = "config." + ".".join(path + [key])
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                if debug_below: print("0")
                merge(a[key], b[key], path + [str(key)], notifier, debug_below=debug_below)
            elif a[key] == b[key]:
                if debug_below: print("1")
                pass # same leaf value
            elif isinstance(a[key], list) and isinstance(b[key], list):
                if debug_below: print("A")
                a_names = {}
                for idx_a, el_a in enumerate(a[key]):
                    if debug_below: print("B")
                    a_names[el_a['name']] = idx_a
                for idx_b, el_b in enumerate(b[key]):
                    if debug_below: print("C")
                    if el_b['name'] in a_names:
                        if debug_below: print("D")
                        merge(el_a, el_b, path + [str(key)] + [str(el_a['name'])], notifier, debug_below=debug_below)
                    else:
                        if debug_below: print("E")
                        a[key] + el_b
                        if debug_below: print("F")
                        if notifier:
                            notifier(path + [str(key)] + [str(el_a['name'])], el_b)
            else:
                if debug_below: print("2")
                a[key] = b[key]
                if notifier:
                    notifier(topic, a[key])
        else:
            if debug_below: print("3")
            a[key] = b[key]
            if notifier:
                notifier(topic, a[key])
    if debug_below: print("Up!")
    return a

def serve_file(path_el):
    path = os.sep.join(path_el)
    headers = {}
    if path.endswith(".png"):
        headers['Content-Type'] = "image/png"
    if path.endswith(".js"):
        headers['Content-Type'] = "text/javascript"

    try:
        with open(path, "rb") as f:
            return (200, headers, f.read())
    except OSError as e:
        return (404, {}, "{} not found".format(path))

@ampule.route("/")
def index(request):
    return serve_file(["web", "index.html"])

@ampule.route("/assets/<subdir>/<filename>")
def files(request, subdir, filename):
    return serve_file(["web", "assets", subdir, filename])

@ampule.route("/assets/<filename>")
def files(request, filename):
    return serve_file(["web", "assets", filename])

@ampule.route("/<filename>")
def files(request, filename):
    return serve_file(["web", filename])

@ampule.route("/api/config")
def get_config(request):
    return (200, {}, json.dumps(request.context.target))

@ampule.route("/api/config", method='POST')
def post_config(request):
    # print(request.body)
    # print("Got config!")
    merge(request.context.target, json.loads(request.body), notifier=request.context.msgbus.pub)
    return (200, {}, json.dumps("OK!"))


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
