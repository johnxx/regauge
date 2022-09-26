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
    # print_dbg("Merging: {}".format(json.dumps(path)))
    if debug_below: 
        print(json.dumps(a))
        print(json.dumps(b))
    for key in b:
        topic = "config." + ".".join(path + [key])
        print("Topic: {}".format(topic))
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
                    if 'name' not in el_a:
                        continue
                    if debug_below: print("B-")
                    # print(str(idx_a))
                    # print(el_a)
                    print("We already have {}".format(el_a['name']))
                    # @TODO: We're not sending the right thing from the client
                    if debug_below: print("B")
                    a_names[el_a['name']] = idx_a
                    if debug_below: print("B+")
                for idx_b, el_b in enumerate(b[key]):
                    if debug_below: print("C")
                    if 'name' not in el_b:
                        continue
                    if el_b['name'] in a_names:
                        print("Got an update for  {}".format(el_b['name']))
                        idx_a = a_names[el_b['name']]
                        if debug_below: print("D")
                        # merge(el_a, el_b, path + [str(key)] + [str(el_a['name'])], notifier, debug_below=debug_below)
                        merge(a[key][idx_a], el_b, path + [str(key)] + [str(el_b['name'])], notifier, debug_below=debug_below)
                    else:
                        print("This is gonna break :(")
                        if debug_below: print("E")
                        a[key] + el_b
                        if debug_below: print("F")
                        if notifier:
                            print("Notify (A): {}.{}.{}: {}".format(path, str(key), str(el_a['name']), el_b))
                            notifier(path + [str(key)] + [str(el_a['name'])], el_b)
            else:
                if debug_below: print("2")
                a[key] = b[key]
                if notifier:
                    print("Notify (B): {}: {}".format(topic, a[key]))
                    notifier(topic, a[key])
        else:
            if debug_below: print("3")
            a[key] = b[key]
            if notifier:
                print("Notify (C): {}: {}".format(topic, a[key]))
                notifier(topic, a[key])
    if debug_below: print("Up!")
    return a

def chunked_read(path, size_k=1):
    size = size_k*1024
    def gennie():
        with open(path, "rb") as f:
            while(True):
                chunk = f.read(size)
                if not chunk:
                    break
                yield chunk
    return gennie

def serve_file(path_el):
    path = os.sep.join(path_el)
    headers = {}
    if path.endswith(".png"):
        headers['Content-Type'] = "image/png"
    if path.endswith(".js"):
        headers['Content-Type'] = "text/javascript"

    try:
        headers["Transfer-Encoding"] = "chunked"
        return (200, headers, chunked_read(path, size_k=8))
        # return (200, headers, chunked_read(f, size_k=1))
        # return (200, headers, f.read())
    except OSError as e:
        return (404, {}, "{} not found".format(path))

@ampule.route("/")
def index(request):
    return serve_file(["web", "index.html"])

@ampule.route("/layout")
def index(request):
    return serve_file(["web", "index.html"])

@ampule.route("/data_sources")
def index(request):
    return serve_file(["web", "index.html"])

@ampule.route("/hardware")
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

@ampule.route("/api/demo")
def get_config(request):
    headers = { 'Access-Control-Allow-Origin': '*' }
    layout = {}
    for block in request.context.target['layout']:
        n = block['name']
        if n not in layout:
            layout[n] = {}
        layout[n] = block['gauge_face']

    return (200, headers, json.dumps({'layout': layout}))

@ampule.route("/api/demo", method='POST')
def post_config(request):
    headers = { 'Access-Control-Allow-Origin': '*' }
    post_data = json.loads(request.body)
    idx = 0
    layout = post_data.pop('layout')
    post_data['layout'] = []
    for key in layout:
        layout_block = {}
        layout_block['name'] = key
        layout_block['gauge_face'] = layout.pop(key)
        post_data['layout'].append(layout_block)
        idx += 1

    merge(request.context.target, post_data, notifier=request.context.msgbus.pub)
    return (200, headers, json.dumps("OK!"))

@ampule.route("/api/demo", method='OPTIONS')
def cors_options(request):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
        'Access-Control-Allow-Headers': 'X-PINGOTHER, Content-Type',
        'Access-Control-Max-Age': 86400
    }
    return (204, headers, '')

@ampule.route("/api/config")
def get_config(request):
    headers = { 'Access-Control-Allow-Origin': '*' }
    return (200, headers, json.dumps(request.context.target))

@ampule.route("/api/config", method='POST')
def post_config(request):
    headers = { 'Access-Control-Allow-Origin': '*' }
    merge(request.context.target, json.loads(request.body), notifier=request.context.msgbus.pub)
    return (200, headers, json.dumps("OK!"))

@ampule.route("/api/config", method='OPTIONS')
def cors_options(request):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
        'Access-Control-Allow-Headers': 'X-PINGOTHER, Content-Type',
        'Access-Control-Max-Age': 86400
    }
    return (204, headers, '')

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
        # print(json.dumps(target))
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
