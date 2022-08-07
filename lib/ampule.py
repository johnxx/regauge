import io
import re
import json
import time
import sys
import traceback

BUFFER_SIZE = 256
TIMEOUT = 30
routes = []
variable_re = re.compile("^<([a-zA-Z]+)>$")

class Request:
    def __init__(self, method, full_path, version="HTTP/1.0"):
        self.method = method
        self.path = full_path.split("?")[0]
        self.version = version
        self.params = Request.__parse_params(full_path)
        self.headers = {}
        self.body = None

    @staticmethod
    def __parse_params(path):
        query_string = path.split("?")[1] if "?" in path else ""
        param_list = query_string.split("&")
        params = {}
        for param in param_list:
            key_val = param.split("=")
            if len(key_val) == 2:
                params[key_val[0]] = key_val[1]
        return params


def __parse_headers(reader):
    headers = {}
    for line in reader:
        if line == b'\r\n': break
        title, content = str(line, "utf-8").split(":", 1)
        headers[title.strip().lower()] = content.strip()
    return headers

def __parse_body(reader):
    data = bytearray()
    for line in reader:
        if line == b'\r\n': break
        data.extend(line)
    return str(data, "utf-8")

def __read_request(client):
    message = bytearray()
    #client.settimeout(30)
    client.settimeout(5)
    socket_recv = True

    try:
        while socket_recv:
            buffer = bytearray(BUFFER_SIZE)
            client.recv_into(buffer)
            start_length = len(message)
            for byte in buffer:
                if byte == 0x00:
                    socket_recv = False
                    break
                else:
                    message.append(byte)
    except OSError as error:
        print("Error reading from socket", error)

    reader = io.BytesIO(message)
    line = str(reader.readline(), "utf-8")
    if line == '':
        raise ValueError("Request was empty")
    (method, full_path, version) = (line.rstrip("\r\n").split(None, 2) + [None, None, None])[:3]

    if not version:
        version = "HTTP/1.0"
    request = Request(method, full_path, version)
    request.headers = __parse_headers(reader)
    request.body = __parse_body(reader)

    return request

def __chunked_response_helper(client, response, data):
    bytes_sent_total = 0
    for chunk in data():

        response.write(b"{}\r\n".format(len(chunk)))
        response.write(chunk)
        response.write(b"\r\n")

        response.flush()
        response_len = response.tell()
        response.seek(0)

        # unreliable sockets on ESP32-S2: see https://github.com/adafruit/circuitpython/issues/4420#issuecomment-814695753
        bytes_sent_chunk = 0
        while True:
            try:
                bytes_sent = client.send(response.read(response_len))
                bytes_sent_chunk += bytes_sent
                if bytes_sent_chunk >= response_len:
                    break
                else:
                    response.seek(bytes_sent_chunk)
                    continue
            except OSError as e:
                if e.errno == 11:       # EAGAIN: no bytes have been transfered
                    continue
                else:
                    break
        bytes_sent_total += bytes_sent_chunk
    return bytes_sent_total

def __fixed_size_response_helper(client, response, data):
        if(isinstance(data, str)):
            response.write(data.encode())
        else:
            response.write(data)
        # response.write(b"\r\n")

        response.flush()
        response.seek(0)
        response_buffer = response.read()

        # unreliable sockets on ESP32-S2: see https://github.com/adafruit/circuitpython/issues/4420#issuecomment-814695753
        response_length = len(response_buffer)
        bytes_sent_total = 0
        while True:
            try:
                bytes_sent = client.send(response_buffer)
                bytes_sent_total += bytes_sent
                if bytes_sent_total >= response_length:
                    return bytes_sent_total
                else:
                    response_buffer = response_buffer[bytes_sent:]
                    continue
            except OSError as e:
                if e.errno == 11:       # EAGAIN: no bytes have been transfered
                    continue
                else:
                    return bytes_sent_total
    
def __send_response(client, code, headers, data):
    if "Transfer-Encoding" in headers and headers["Transfer-Encoding"] == 'chunked':
        chunked = True

    else:
        headers["Content-Length"] = len(data)
        chunked = False
    headers["Server"] = "Ampule/0.0.1-alpha (CircuitPython)"
    headers["Connection"] = "close"
    with io.BytesIO() as response:
        response.write(("HTTP/1.1 %i OK\r\n" % code).encode())
        for k, v in headers.items():
            response.write(("%s: %s\r\n" % (k, v)).encode())

        response.write(b"\r\n")

        if chunked:
            return __chunked_response_helper(client, response, data)
        else:
            return __fixed_size_response_helper(client, response, data)

def __on_request(method, rule, request_handler):
    regex = "^"
    rule_parts = rule.split("/")
    for part in rule_parts:
        # Is this portion of the path a variable?
        var = variable_re.match(part)
        if var:
            # If so, allow any alphanumeric value
            regex += r"([a-zA-Z0-9_.-]+)\/"
        else:
            # Otherwise exact match
            regex += part + r"\/"
    regex += "?$"
    routes.append(
        (re.compile(regex), {"method": method, "func": request_handler})
    )

def __match_route(path, method):
    for matcher, route in routes:
        match = matcher.match(path)
        if match and method == route["method"]:
            return (match.groups(), route)
    return None

def listen(socket, context=None, timeout=30):
    client, remote_address = socket.accept()
    log_level = 6
    try:
        client.settimeout(timeout)
        request = __read_request(client)
        if context:
            request.context = context
        match = __match_route(request.path, request.method)
        if match:
            args, route = match
            status, headers, body = route["func"](request, *args)
            total_transferred = __send_response(client, status, headers, body)
        else:
            total_transferred = __send_response(client, 404, {}, "Not found")
        if log_level >= 6:
            print("ampule: {} - friend [{}] \"{} {} {}\" {} {}"
                .format(
                    remote_address[0],
                    time.monotonic(),
                    request.method,
                    request.path,
                    request.version,
                    status,
                    total_transferred
                )
            )
    except BaseException as e:
        print("Error with request: {}: {}".format(type(e), e))
        # print(json.dumps(e.__traceback__.tb_frame.__dict__))
        # trace = []
        # ex = e
        # tb = ex.__traceback__
        # while tb is not None:
        #     trace.append({
        #         "filename": tb.tb_frame.f_code.co_filename,
        #         "name": tb.tb_frame.f_code.co_name,
        #         "lineno": tb.tb_lineno
        #     })
        #     tb = tb.tb_next
        # print(str({
        #     'type': type(ex).__name__,
        #     'message': str(ex),
        #     'trace': trace
        # }))
        # print(json.dumps(e.__traceback__.tb_lineno))
        # print("Error with request", str(e))
        # print("Error with request:", str(json.dumps(e)))
        #traceback.print_exception(None, e, sys.exc_info()[2])
        __send_response(client, 500, {}, "Error processing request")
    finally:
        if log_level >= 7:
            print("Closing connection")
        client.close()

def route(rule, method='GET'):
    return lambda func: __on_request(method, rule, func)
