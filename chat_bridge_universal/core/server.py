import socket
from enum import unique, auto
from typing import cast

from chat_bridge_universal.core.basic import CBUBase, Address
from chat_bridge_universal.core.config import CBUConfigBase, load_config
from chat_bridge_universal.core.state import CBUStateBase


class CBUServerConfig(CBUConfigBase):
    hostname: str = 'localhost'
    port: int = 30001

    @property
    def address(self) -> Address:
        return Address(hostname=self.hostname, port=self.port)


@unique
class CBUServerState(CBUStateBase):
    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()


class CBUServer(CBUBase):
    def __init__(self, config_path: str):
        super().__init__(load_config(config_path, CBUServerConfig))
        self.config: CBUServerConfig = cast(CBUServerConfig, self.config)
        self._state = CBUServerState.STOPPED
        self.__should_loop_console = True

    def _get_logger_name(self):
        return 'Server'

    def _get_main_loop_thread_name(self):
        return 'ServerThread'

    def _main_loop(self):
        self.assert_state(CBUServerState.STOPPED)
        self._set_state(CBUServerState.STARTING)
        try:
            self._sock.bind(self.config.address)
        except socket.error:
            self.logger.error('Failed to bind {}'.format(self.config.address))
            return

        try:
            self._sock.listen(5)
            self._sock.settimeout(3)
            self.logger.info('Server started @ {}'.format(self.config.address))
            self.logger.info('Waiting for connections')
            self._set_state(CBUServerState.RUNNING)
            while self.is_running():
                try:
                    try:
                        conn, addr = self._sock.accept()
                    except socket.timeout:
                        pass
                except Exception as e:
                    if self.is_running():
                        self.logger.exception('Error ticking server: {}'.format(e))
        finally:
            self._stop()
        self.logger.info('bye')

    def is_running(self):
        return self.in_state(CBUServerState.RUNNING)

    def _stop(self):
        super()._stop()
        self._set_state(CBUServerState.STOPPED)
        self.__should_loop_console = False

    def console_loop(self):
        while self.__should_loop_console:
            input_ = input()
            if input_ == 'stop':
                self.stop()

    def start(self):
        super().start()
        self.console_loop()
