import socket
from enum import auto
from threading import Event, Thread
from typing import cast, Dict, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter

from chat_bridge_universal.core.basic import StateBase, CBUBaseConfigured, CBUBase
from chat_bridge_universal.core.config import CBUServerConfig, Address, ClientMeta
from chat_bridge_universal.core.network import net_util
from chat_bridge_universal.core.network.cryptor import AESCryptor
from chat_bridge_universal.core.network.protocal import LoginPacket, LoginResultPacket


class CBUServerState(StateBase):
    STOPPED = auto()  # stopped
    STARTING = auto()  # binding socket, setup
    RUNNING = auto()  # running


class CBUServer(CBUBaseConfigured):
    def __init__(self, config_path: str):
        super().__init__(config_path, CBUServerConfig)
        self.config = cast(CBUServerConfig, self.config)
        completer = WordCompleter(['stop', 'send', 'list', 'help'])
        self.__prompt_session = PromptSession(completer=completer)
        self.__binding_done = Event()
        self._state = CBUServerState.STOPPED
        self.__clients: Dict[str, ClientConnection] = {}
        for client in self.config.clients:
            self.__clients[client.name] = ClientConnection(client, self._cryptor)

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
        client = self.__clients.get(packet.name)
        if client.meta.password == packet.password:
            self.logger.info('Identification of {} confirmed: {}'.format(addr, client.meta.name))
            client.open_connection(conn, addr)
        else:
            self.logger.warning(
                'Wrong password during login for client {}: expected {} but received {}'.format(client.meta.name,
                                                                                                client.meta.password,
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
            self.logger.info('Handling user input: {}'.format(text))
            if text == 'stop':
                self.stop()

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


class ClientConnection(CBUBase):
    def __init__(self, meta: ClientMeta, cryptor: AESCryptor):
        super().__init__(cryptor)
        self.meta = meta
        self.__server_address: Optional[Address] = None

    def open_connection(self, conn: socket.socket, address: Address):
        self._sock = conn
        self.__server_address = address
        self._send_packet(LoginResultPacket(success=True))


if __name__ == '__main__':
    CBUServer('../server_config.json').start()
