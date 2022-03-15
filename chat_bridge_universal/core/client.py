import socket
from threading import Event
from typing import Optional, cast

from chat_bridge_universal.core.basic import CBUBase
from chat_bridge_universal.core.config import CBUClientConfig


class CBUClient(CBUBase):
    def __init__(self, config_path: str):
        super().__init__(config_path, CBUClientConfig)
        self.config = cast(CBUClientConfig, self.config)
        self.__sock: Optional[socket.socket] = None
        self.__connection_done = Event()
        self._stopped = True

    def get_main_thread_name(self) -> str:
        return 'ClientThread'

    def get_logger_name(self) -> str:
        return 'Client'

    def __connect(self):
        self.__sock.connect(self.config.server_address)

    def _main_loop(self):
        self.__sock = socket.socket()
        try:
            self.__connect()
        except socket.error:
            self.__stopped = True
            self.logger.error('Failed to connect to {}'.format(self.config.server_address))
            return
        finally:
            self.__stopped = False
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
        self.__stopped = True
        if self.__sock is not None:
            self.__sock.close()
            self.__sock = None
            self.logger.info('Socket closed')


if __name__ == '__main__':
    CBUClient('../../client_config.json').start()
