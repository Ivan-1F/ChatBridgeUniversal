import socket
from enum import unique, auto
from threading import Event
from typing import cast, Iterable

from chat_bridge_universal.core.basic import StateBase, CBUBase, Configurable
from chat_bridge_universal.core.config import CBUClientConfig
from chat_bridge_universal.core.network import net_util
from chat_bridge_universal.core.network.protocal import LoginPacket, LoginResultPacket, ChatPacket, ChatPayload, \
    AbstractPayload


@unique
class CBUClientState(StateBase):
    STARTING = auto()  # thread started
    CONNECTING = auto()  # socket connecting
    CONNECTED = auto()  # socket connected, logging in
    ONLINE = auto()  # logged in, thread started
    DISCONNECTED = auto()  # socket disconnected, cleaning threads
    STOPPED = auto()  # stopped


class CBUClient(CBUBase, Configurable):
    def __init__(self, config_path: str):
        Configurable.__init__(self, config_path, CBUClientConfig)
        CBUBase.__init__(self, self.config.aes_key)
        self.config = cast(CBUClientConfig, self.config)
        self.__connection_done = Event()
        self.__state: CBUClientState = CBUClientState.STOPPED

    def get_main_thread_name(self) -> str:
        return 'ClientThread'

    def get_logger_name(self) -> str:
        return 'Client'

    def is_stopped(self) -> bool:
        return self.in_state({CBUClientState.STOPPED})

    def is_online(self) -> bool:
        return self.in_state({CBUClientState.ONLINE})

    def __build_and_send_packet(self, receiver: Iterable[str], payload: AbstractPayload, *,
                                is_broadcast: bool):
        self._send_packet(ChatPacket(
            sender=self.config.name,
            receivers=list(receiver),
            broadcast=is_broadcast,
            payload=payload.serialize()
        ))

    def _on_packet(self, packet: ChatPacket):
        self.on_chat(packet.sender, ChatPayload.deserialize(packet.payload))

    def on_chat(self, sender: str, payload: ChatPayload):
        self.logger.debug('Received chat packet: [{}] '.format(sender) + payload.formatted_str)
        pass

    def send_chat(self, message: str, author: str = ''):
        self.send_to_all(ChatPayload(author=author, message=message))

    def send_to_all(self, payload: AbstractPayload):
        self.__build_and_send_packet([], payload, is_broadcast=True)

    def __connect_and_login(self):
        self.assert_state(CBUClientState.STARTING)
        self.__connect()
        self.logger.debug('Connected to the server, sending login packet')
        self._send_packet(LoginPacket(name=self.config.name, password=self.config.password))
        result = self._receive_packet(LoginResultPacket)
        if result.success:
            self._set_state(CBUClientState.ONLINE)
        else:
            raise ConnectionError('Failed to login to the server')

    def __connect(self):
        self._set_state(CBUClientState.CONNECTING)
        self._sock.connect(self.config.server_address)
        self._set_state(CBUClientState.CONNECTED)

    def _tick_connection(self):
        try:
            packet = self._receive_packet(ChatPacket)
        except socket.timeout:
            pass
        else:
            try:
                self._on_packet(packet)
            except Exception as e:
                self.logger.exception('Fail to process packet {}: {}'.format(packet, e))

    def _main_loop(self):
        self._sock = socket.socket()
        self._set_state(CBUClientState.STARTING)
        try:
            self.__connect_and_login()
        except Exception as e:
            self._set_state(CBUClientState.STOPPED)
            self.logger.error('Failed to connect to {}: {}'.format(self.config.server_address, e))
            self.__connection_done.set()
            return
        else:
            self.logger.info('Logged in to the server')
            self.__connection_done.set()
            while self.is_online():
                try:
                    self._tick_connection()
                except (ConnectionResetError, net_util.EmptyContent) as e:
                    self.logger.warning('Connection closed: {}'.format(e))
                    break
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
        self._set_state(CBUClientState.STOPPED)
        if self._sock is not None:
            self._sock.close()
            self._sock = None
            self.logger.info('Socket closed')


if __name__ == '__main__':
    CBUClient('../../client_config.json').start()
