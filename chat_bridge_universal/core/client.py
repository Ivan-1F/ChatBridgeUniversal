import socket
from enum import unique, auto
from threading import Event
from typing import cast

from chat_bridge_universal.core.basic import CBUBase, StateBase
from chat_bridge_universal.core.config import CBUClientConfig
from chat_bridge_universal.core.network.protocal import LoginPacket, LoginResultPacket


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
        self.__connection_done = Event()
        self.__state: CBUClientState = CBUClientState.STOPPED

    def get_main_thread_name(self) -> str:
        return 'ClientThread'

    def get_logger_name(self) -> str:
        return 'Client'

    def is_stopped(self) -> bool:
        return self.in_state({CBUClientState.STOPPED})

    def _is_connected(self) -> bool:
        return self.in_state({CBUClientState.CONNECTED, CBUClientState.ONLINE})

    def __connect_and_login(self):
        self.assert_state(CBUClientState.STARTING)
        self.__connect()
        self.logger.debug('Sending login packet')
        self._send_packet(LoginPacket(name=self.config.name, password=self.config.password))
        self.logger.debug('Waiting for login result')
        result = self._receive_packet(LoginResultPacket)
        if result.success:
            self._set_state(CBUClientState.ONLINE)
            self.logger.info('Logged in to the server')
        else:
            self.logger.info('Failed to login to the server')

    def __connect(self):
        self._set_state(CBUClientState.CONNECTING)
        self._sock.connect(self.config.server_address)
        self._set_state(CBUClientState.CONNECTED)

    def _main_loop(self):
        self._sock = socket.socket()
        self._set_state(CBUClientState.STARTING)
        try:
            self.__connect_and_login()
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
        self.logger.debug('Started client')

    def stop(self):
        self.__stop()
        super().stop()

    def __stop(self):
        self._set_state(CBUClientState.STOPPED)
        if self._sock is not None:
            self._sock.close()
            self._sock = None
            self.logger.info('Socket closed')


if __name__ == '__main__':
    CBUClient('../../client_config.json').start()
