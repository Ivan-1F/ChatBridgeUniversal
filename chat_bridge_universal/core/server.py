import socket
from enum import Enum, unique
from threading import Thread
from typing import Iterable, Callable

from chat_bridge_universal.common import constants
from chat_bridge_universal.core.basic import ChatBridgeUniversalBase
from chat_bridge_universal.core.config import ChatBridgeUniversalServerConfig, load_config
from chat_bridge_universal.core.network.basic import Address


@unique
class CBUServerState(Enum):
    STOPPED = 'cbu.state.stopped'
    STARTING = 'cbu.state.starting'
    RUNNING = 'cbu.state.running'

    def in_state(self, states):
        if type(states) is type(self):
            return self is states
        elif not isinstance(states, Iterable):
            states = (states,)
        return self in states


class ChatBridgeUniversalServer(ChatBridgeUniversalBase):
    def __init__(self, config_path: str):
        super().__init__('Server')
        self.config = load_config(config_path, ChatBridgeUniversalServerConfig)
        self.__sock = socket.socket()
        self.state = CBUServerState.STOPPED

    def set_state(self, state: CBUServerState):
        self.state = state

    def in_state(self, state):
        return self.state.in_state(state)

    def is_running(self):
        return self.state.in_state({CBUServerState.RUNNING})

    def __handle_connection(self, conn, address: Address):
        pass

    def start(self):
        self.set_state(CBUServerState.STARTING)
        try:
            self.__sock.bind(self.config.address)
        except socket.error:
            self.logger.error('Failed to bind {}'.format(self.config.address))
            self.set_state(CBUServerState.STOPPED)
            return

        try:
            self.__sock.listen(5)
            self.__sock.settimeout(3)
            self.logger.info('{} server started at {}'.format(constants.NAME, self.config.address))
            self.logger.info('Waiting for connections...')
            self.set_state(CBUServerState.RUNNING)
            connection_id = 0
            while self.is_running():
                try:
                    conn, addr = self.__sock.accept()
                except socket.timeout:
                    continue
                address = Address(*addr)
                self.logger.info('New connection #{} from {}'.format(connection_id, address))
                Thread(
                    name='Connection#{}'.format(connection_id),
                    target=self.__handle_connection, args=(conn, address),
                    daemon=True
                ).start()

        finally:
            self.stop()
        self.logger.info('bye')

    def stop(self):
        self.__sock.close()
        self.set_state(CBUServerState.STOPPED)
