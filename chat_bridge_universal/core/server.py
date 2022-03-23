import socket
from enum import unique, auto
from threading import Thread
from typing import cast, Dict, List

from chat_bridge_universal.core.basic import CBUBase, Address
from chat_bridge_universal.core.client import CBUClient, CBUClientConfig
from chat_bridge_universal.core.config import CBUConfigBase, load_config, ClientMeta
from chat_bridge_universal.core.network import network_utils
from chat_bridge_universal.core.network.protocal import LoginPacket, LoginResultPacket, ChatPacket
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
        login_packet = network_utils.receive_packet(conn, self._cryptor, LoginPacket)
        if login_packet.name not in self.__connections:
            self.logger.warning('Unknown client: {} from {}'.format(login_packet.name, address))
            return
        connection = self.__connections.get(login_packet.name)
        if connection.config.password == login_packet.password:
            self.logger.info('Identification of {} confirmed: {}'.format(address, connection.config.name))
            network_utils.send_packet(conn, self._cryptor, LoginResultPacket(success=True, message='ok'))
            # self._send_packet(LoginResultPacket(success=True, message='ok'))
            connection.open(conn)
        else:
            self.logger.warning('Wrong password during login for client {}: expected {} but received {}'.format(connection.config.name, connection.config.password, login_packet.password))
            network_utils.send_packet(conn, self._cryptor, LoginResultPacket(success=False, message='Password incorrect'))
            # self._send_packet(LoginResultPacket(success=False, message='Password incorrect'))

    def _main_loop(self):
        self.assert_state(CBUServerState.STOPPED)
        self._set_state(CBUServerState.STARTING)
        try:
            self._sock.bind(self.config.address)
        except socket.error:
            self.logger.error('Failed to bind {}'.format(self.config.address))
            self._stop()
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

    def process_packet(self, packet: ChatPacket):
        self.logger.info('Received chat from {}: {}'.format(packet.sender, packet.serialize()))
        for connection in self.__connections.values():
            if connection.is_online():
                if packet.broadcast or connection.config.name in packet.receivers:
                    if connection.config.name != packet.sender:  # do not send the message to the sender
                        connection.send_packet(packet)


class ClientConnection(CBUClient):
    def __init__(self, server: CBUServer, meta: ClientMeta):
        self.__meta = meta
        self.__server = server
        super().__init__(CBUClientConfig(aes_key=server.config.aes_key, name=meta.name, password=meta.password,
                                         server_hostname=server.config.hostname, server_port=server.config.port))

    def open(self, conn: socket.socket):
        self._sock = conn
        self.start()

    def _on_packet(self, packet: ChatPacket):
        super()._on_packet(packet)
        self.__server.process_packet(packet)

    def _connect_and_login(self):
        pass

    def _get_logger_name(self) -> str:
        return 'Server.{}'.format(self.__meta.name)

    def _get_main_loop_thread_name(self):
        return super()._get_main_loop_thread_name() + '.' + self.__meta.name
