import socket

from chat_bridge_universal.core.basic import CBUBase
from chat_bridge_universal.core.config import CBUServerConfig, Address


class CBUServer(CBUBase):
    config: CBUServerConfig

    def __init__(self, config_path: str):
        super().__init__(config_path, CBUServerConfig)
        self.__sock = socket.socket()

    def get_main_thread_name(self) -> str:
        return 'ServerThread'

    def _main_loop(self):
        try:
            self.__sock.bind(self.config.address)
        except socket.error:
            raise RuntimeError('Failed to bind {}'.format(self.config.address))

        try:
            self.__sock.listen(5)
            self.__sock.settimeout(3)
            self.logger.info('Server started at {}'.format(self.config.address))
            while True:
                try:
                    try:
                        conn, addr = self.__sock.accept()
                    except socket.timeout:
                        continue

                    address = Address(*addr)
                    self.logger.info('New connection #{} from {}'.format(counter, address))
                except socket.timeout:
                    continue
        finally:
            self.__stop()
        self.logger.info('bye')

    def __stop(self):
        pass


if __name__ == '__main__':
    CBUServer('../server_config.json').start()
