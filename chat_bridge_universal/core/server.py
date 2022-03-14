import socket

from chat_bridge_universal.common import constants
from chat_bridge_universal.core.basic import ChatBridgeUniversalBase
from chat_bridge_universal.core.config import ChatBridgeUniversalServerConfig, load_config
from chat_bridge_universal.core.network.basic import Address


class ChatBridgeUniversalServer(ChatBridgeUniversalBase):
    def __init__(self, config_path: str):
        super().__init__('Server')
        self.config = load_config(config_path, ChatBridgeUniversalServerConfig)
        self.__sock = socket.socket()

    def start(self):
        try:
            self.__sock.bind(self.config.address)
        except socket.error:
            self.logger.error('Failed to bind {}'.format(self.config.address))

        try:
            self.__sock.listen(5)
            # self.__sock.settimeout(3)
            self.logger.info('{} server started at {}'.format(constants.NAME, self.config.address))
            connection_id = 0
            while True:
                conn, addr = self.__sock.accept()
                address = Address(*addr)
                self.logger.info('New connection: ', address)
                pass
        finally:
            pass
        self.logger.info('bye')
