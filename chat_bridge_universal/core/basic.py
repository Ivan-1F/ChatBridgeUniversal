import socket
from typing import Optional

from chat_bridge_universal.common.logger import ChatBridgeUniversalLogger


class ChatBridgeUniversalBase:
    def __init__(self, name: str):
        self.__name = name
        self._sock: Optional[socket.socket] = None
        self.logger = ChatBridgeUniversalLogger(self.get_logging_name())

    def get_name(self) -> str:
        return self.__name

    def get_logging_name(self) -> str:
        return self.get_name()

    def _set_socket(self, sock: socket.socket):
        self._sock = sock
