import socket
from threading import Event, Thread
from typing import cast

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter

from chat_bridge_universal.core.basic import CBUBase
from chat_bridge_universal.core.config import CBUServerConfig, Address
from chat_bridge_universal.core.network.protocal import LoginPacket


class CBUServer(CBUBase):
    def __init__(self, config_path: str):
        super().__init__(config_path, CBUServerConfig)
        self.config = cast(CBUServerConfig, self.config)
        completer = WordCompleter(['stop', 'send', 'list', 'help'])
        self.__prompt_session = PromptSession(completer=completer)
        self.__binding_done = Event()
        self.__stopped = True

    def get_main_thread_name(self) -> str:
        return 'ServerThread'

    def get_logger_name(self) -> str:
        return 'Server'

    def __handle_connection(self, conn: socket, addr: Address):
        packet = self._receive_packet(LoginPacket)
        client = list(filter(lambda x: x.name == packet.name, self.config.clients))[0]
        if client.password == packet.password:
            self.logger.info('Identification of {} confirmed: {}'.format(addr, client.name))
        else:
            self.logger.warning(
                'Wrong password during login for client {}: expected {} but received {}'.format(client.name,
                                                                                                client.password,
                                                                                                packet.password))

    def _main_loop(self):
        self._sock = socket.socket()
        try:
            self._sock.bind(self.config.address)
        except socket.error:
            self.__stopped = True
            self.logger.error('Failed to bind {}'.format(self.config.address))
            return
        finally:
            self.__stopped = False
            self.__binding_done.set()

        try:
            self._sock.listen(5)
            self._sock.settimeout(3)
            self.logger.info('Server started at {}'.format(self.config.address))
            while not self.__stopped:
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
                except:
                    if not self.__stopped:
                        self.logger.exception('Error ticking server')
        finally:
            self.__stop()
        self.logger.info('bye')

    def start(self):
        self.__binding_done.clear()
        super().start()
        self.__binding_done.wait()
        self.prompt_loop()

    def prompt_loop(self):
        while not self.__stopped:
            text = self.__prompt_session.prompt('> ')
            self.logger.info('Handling user input: {}'.format(text))
            if text == 'stop':
                self.stop()

    def stop(self):
        self.__stop()
        super().stop()

    def __stop(self):
        self.__stopped = True
        if self._sock is not None:
            self._sock.close()
            self._sock = None
            self.logger.info('Socket closed')


if __name__ == '__main__':
    CBUServer('../server_config.json').start()
