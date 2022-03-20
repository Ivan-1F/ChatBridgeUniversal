import socket
from enum import unique, auto
from threading import Thread
from typing import cast, Dict, List

from chat_bridge_universal.core.basic import CBUBase, Address
from chat_bridge_universal.core.client import CBUClient, CBUClientConfig
from chat_bridge_universal.core.config import CBUConfigBase, load_config, ClientMeta
from chat_bridge_universal.core.state import CBUStateBase


class CBUServerConfig(CBUConfigBase):
    hostname: str = 'localhost'
    port: int = 30001

    clients: List[ClientMeta] = [
        ClientMeta(name='MyClientName', password='MyClientPassword')
    ]

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
        self.__connections: Dict[str, ClientConnection] = {}
        for client in self.config.clients:
            self.__connections[client.name] = ClientConnection(self, client)

    def _get_logger_name(self):
        return 'Server'

    def _get_main_loop_thread_name(self):
        return 'ServerThread'

    def __handle_connection(self, conn: socket.socket, address: Address):
        # receive login packet, confirm identity
        # get connection from self.__connection and call ClientConnection#open
        pass

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
                counter = 0
                try:
                    try:
                        conn, addr = self._sock.accept()
                        address = Address(*addr)
                        self.logger.info('New connection #{} from {}'.format(counter, address))
                        Thread(name='Connection#{}'.format(counter), target=self.__handle_connection,
                               args=(conn, address),
                               daemon=True).start()
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


class ClientConnection(CBUClient):
    def __init__(self, server: CBUServer, meta: ClientMeta):
        super().__init__(CBUClientConfig(aes_key=server.config.aes_key, name=meta.name, password=meta.password,
                                         server_hostname=server.config.hostname, server_port=server.config.port))
        self.__meta = meta

    def open(self, conn: socket.socket, address: Address):
        self._sock = conn
        self._connect(address)
