import socket
from typing import NamedTuple, Optional


class Address(NamedTuple):
    hostname: str
    port: int

    def __str__(self):
        return '{}:{}'.format(self.hostname, self.port)


class NetworkComponent:
    def __init__(self):
        self.sock: Optional[socket.socket] = None

    def set_socket(self, sock: socket.socket):
        self.sock = sock
