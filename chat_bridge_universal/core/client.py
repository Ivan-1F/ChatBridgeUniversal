import socket
from enum import unique, auto
from threading import Event
from typing import Optional, cast

from chat_bridge_universal.core.basic import CBUBase, StateBase
from chat_bridge_universal.core.config import CBUClientConfig


@unique
class CBUClientState(StateBase):
    STARTING = auto()  # thread started
    CONNECTING = auto()  # socket connecting
    CONNECTED = auto()  # socket connected, logging in
    ONLINE = auto()  # logged in, thread started
    DISCONNECTED = auto()  # socket disconnected, cleaning threads
    STOPPED = auto()  # stopped


class CBUClient(CBUBase):
    def __init__(self, config_path: str):
        super().__init__(config_path, CBUClientConfig)
        self.config = cast(CBUClientConfig, self.config)
        self.__sock: Optional[socket.socket] = None
        self.__connection_done = Event()
        self.__state: CBUClientState = CBUClientState.STOPPED

    def get_main_thread_name(self) -> str:
        return 'ClientThread'

    def get_logger_name(self) -> str:
        return 'Client'

    def is_stopped(self) -> bool:
        return self.in_state({CBUClientState.STOPPED})

    def __connect(self):
        self._set_state(CBUClientState.CONNECTING)
        self.__sock.connect(self.config.server_address)
        self._set_state(CBUClientState.CONNECTED)

    def _main_loop(self):
        self.__sock = socket.socket()
        self._set_state(CBUClientState.STARTING)
        try:
            self.__connect()
        except socket.error:
            self._set_state(CBUClientState.STOPPED)
            self.logger.error('Failed to connect to {}'.format(self.config.server_address))
            return
        finally:
            self.__connection_done.set()
        try:
            self.logger.info('Connected to {}'.format(self.config.server_address))
        finally:
            self.__stop()
        self.logger.info('bye')

    def start(self):
        self.__connection_done.clear()
        super().start()
        self.__connection_done.wait()

    def stop(self):
        self.__stop()
        super().stop()

    def __stop(self):
        self._set_state(CBUClientState.STOPPED)
        if self.__sock is not None:
            self.__sock.close()
            self.__sock = None
            self.logger.info('Socket closed')


if __name__ == '__main__':
    CBUClient('../../client_config.json').start()
