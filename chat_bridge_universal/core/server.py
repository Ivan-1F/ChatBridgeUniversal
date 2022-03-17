import socket
from enum import auto
from threading import Event, Thread
from typing import cast, Dict, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter

from chat_bridge_universal.core.basic import StateBase, CBUBase, FileConfigurable
from chat_bridge_universal.core.config import CBUServerConfig, Address, ClientMeta
from chat_bridge_universal.core.network import net_util
from chat_bridge_universal.core.network.cryptor import AESCryptor
from chat_bridge_universal.core.network.protocal import LoginPacket, LoginResultPacket, ChatPacket, AbstractPacket, \
    ChatPayload


class CBUServerState(StateBase):
    STOPPED = auto()  # stopped
    STARTING = auto()  # binding socket, setup
    RUNNING = auto()  # running


class CBUServer(CBUBase, FileConfigurable):
    def __init__(self, config_path: str):
        FileConfigurable.__init__(self, config_path, CBUServerConfig)
        CBUBase.__init__(self, self.config.aes_key)
        self.config = cast(CBUServerConfig, self.config)
        completer = WordCompleter(['stop', 'list', 'help'])
        self.__prompt_session = PromptSession(completer=completer)
        self.__binding_done = Event()
        self._state = CBUServerState.STOPPED
        self.__connections: Dict[str, ClientConnection] = {}
        for connection in self.config.clients:
            self.__connections[connection.name] = ClientConnection(connection, self._cryptor, self)

    def get_main_thread_name(self) -> str:
        return 'ServerThread'

    def get_logger_name(self) -> str:
        return 'Server'

    def is_running(self) -> bool:
        return self.in_state(CBUServerState.RUNNING)

    def is_stopped(self) -> bool:
        return self.in_state(CBUServerState.STOPPED)

    def __handle_connection(self, conn: socket.socket, addr: Address):
        packet = net_util.receive_packet(conn, self._cryptor, LoginPacket, timeout=15)
        connection = self.__connections.get(packet.name)
        if connection.meta.password == packet.password:
            self.logger.info('Identification of {} confirmed: {}'.format(addr, connection.meta.name))
            connection.open_connection(conn, addr)
        else:
            self.logger.warning(
                'Wrong password during login for client {}: expected {} but received {}'.format(connection.meta.name,
                                                                                                connection.meta.password,
                                                                                                packet.password))

    def __bind(self):
        self._sock = socket.socket()
        try:
            self._sock.bind(self.config.address)
        except socket.error:
            self.logger.error('Failed to bind {}'.format(self.config.address))
            raise
        finally:
            self.__binding_done.set()

    def __get_connected_connections(self):
        return list(filter(lambda x: x.is_connected(), self.__connections.values()))

    def process_packet(self, packet: ChatPacket):
        self.logger.debug('Received chat packet from {}: {}'.format(packet.sender, ChatPayload.deserialize(
            packet.payload).formatted_str))
        for connection in self.__get_connected_connections():
            connection.send_packet_invoker(packet)

    def _main_loop(self):
        self._state = CBUServerState.STARTING
        try:
            self.__bind()
        except socket.error:
            self.__stop()
            return

        try:
            self._sock.listen(5)
            self._sock.settimeout(3)
            self.logger.info('Server started at {}'.format(self.config.address))
            self._set_state(CBUServerState.RUNNING)

            while self.is_running():
                counter = 0
                try:
                    try:
                        conn, addr = self._sock.accept()
                    except socket.timeout:
                        continue
                    address = Address(*addr)
                    counter += 1
                    self.logger.info('New connection #{} from {}'.format(counter, address))
                    Thread(name='Connection#{}'.format(counter), target=self.__handle_connection, args=(conn, address),
                           daemon=True).start()
                except Exception as e:
                    if not self.is_running():
                        self.logger.exception('Error ticking server: {}'.format(e))
        finally:
            self.__stop()
        self.logger.info('bye')

    def start(self):
        self.__binding_done.clear()
        # Non-block, mainloop started in ServerThread
        super().start()
        self.__binding_done.wait()
        self.prompt_loop()

    def prompt_loop(self):
        while not self.is_stopped():
            text = self.__prompt_session.prompt('> ')
            self.logger.debug('Handling user input: {}'.format(text))
            if text == 'stop':
                self.stop()
            elif text == 'list':
                if len(self.__get_connected_connections()) == 0:
                    self.logger.info('No online client')
                else:
                    self.logger.info('Online clients:')
                    for connection in self.__get_connected_connections():
                        self.logger.info(' - {}'.format(connection.meta.name))
            elif text.startswith('stop') and text.find(' ') != -1:
                target_name = text.split(' ', 1)[1]
                connection = self.__connections.get(target_name)
                if connection is not None:
                    if connection.is_connected():
                        self.logger.info('Stopping client {}'.format(target_name))
                        connection.stop()
                    else:
                        self.logger.warning('Client {} is not connected'.format(target_name))
                else:
                    self.logger.warning('Client {} is not found'.format(target_name))
            elif text == 'help':
                self.logger.info('stop: stop the server')
                self.logger.info('list: list online clients')
                self.logger.info('stop <client_name>: stop a client')
            else:
                self.logger.warning('Invalid command: {}, type \'help\' for help'.format(text))

    def stop(self):
        self.__stop()
        super().stop()

    def __stop(self):
        """
        Internal cleanup
        """
        self._set_state(CBUServerState.STOPPED)
        if self._sock is not None:
            self._sock.close()
            self._sock = None
            self.logger.info('Socket closed')

    def get_logger(self) -> CBULogger:
        return self.logger


class ClientConnection(CBUBase):
    def __init__(self, meta: ClientMeta, cryptor: AESCryptor, server: CBUServer):
        self.meta = meta
        self.server = server
        self.__server_address: Optional[Address] = None
        self.__stop_flag = False
        super().__init__(cryptor)

    def open_connection(self, conn: socket.socket, address: Address):
        self._sock = conn
        self.__server_address = address
        self._send_packet(LoginResultPacket(success=True))
        self.start()

    def get_main_thread_name(self) -> str:
        return self.server.get_main_thread_name() + '.' + self.meta.name

    def get_logger_name(self) -> str:
        return 'Server.{}'.format(self.meta.name)

    def _on_packet(self, packet: ChatPacket):
        self.server.process_packet(packet)

    def _tick_connection(self):
        try:
            packet = self._receive_packet(ChatPacket)
        except socket.timeout:
            pass
        else:
            self._on_packet(packet)

    def _main_loop(self):
        self.__stop_flag = False
        while not self.__stop_flag:
            try:
                self._tick_connection()
            except (ConnectionResetError, net_util.EmptyContent) as e:
                self.logger.warning('Connection closed: {}'.format(e))
                break
        self.stop()
        self.logger.info('bye')

    def is_connected(self):
        return self._sock is not None

    def stop(self):
        self.__stop()
        super().stop()

    def __stop(self):
        self.__stop_flag = True
        if self._sock is not None:
            self._sock.close()
            self._sock = None
            self.logger.info('Socket closed')
        self.__server_address = None

    def send_packet_invoker(self, packet: AbstractPacket):
        self._send_packet(packet)


if __name__ == '__main__':
    CBUServer('../server_config.json').start()
