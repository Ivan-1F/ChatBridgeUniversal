import socket
from typing import Optional, cast

from chat_bridge_universal.core.basic import CBUBase
from chat_bridge_universal.core.config import CBUClientConfig


class CBUClient(CBUBase):
    def __init__(self, config_path: str):
        super().__init__(config_path, CBUClientConfig)
        self.config = cast(CBUClientConfig, self.config)
        self.__sock: Optional[socket.socket] = None

    def get_main_thread_name(self) -> str:
        return 'ClientThread'

    def get_logger_name(self) -> str:
        return 'Client'

    def __connect(self):
        self.__sock.connect(self.config.server_address)

    def _main_loop(self):
        try:
            self.__connect()
        except socket.error:
            self.logger.error('Failed to connect to {}'.format(self.config.server_address))
            return

        self.logger.info('Connected to {}'.format(self.config.server_address))


if __name__ == '__main__':
    CBUClient('../../client_config.json').start()
