class ListenServer:
    def __init__(self, name, resources, target, bind_addr, listen_port, listeners=5, poll_freq=30) -> None:
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
        try:
            connected_sock, remote_addr = self.listen_sock.accept()
            with connected_sock:
                payload = self.receive(connected_sock)
            self.handle(payload)
        except OSError as e:
            if e.errno == 11:
                pass
            else:
                print(e)