from enum import auto, unique
from typing import cast

from chat_bridge_universal.core.basic import CBUBase, Address
from chat_bridge_universal.core.config import CBUConfigBase, ClientMeta
from chat_bridge_universal.core.network.protocal import LoginPacket, LoginResultPacket
from chat_bridge_universal.core.state import CBUStateBase


class CBUClientConfig(CBUConfigBase):
    name: str = 'MyClientName'
    password: str = 'MyClientPassword'
    server_hostname: str = '127.0.0.1'
    server_port: int = 30001

    @property
    def client_meta(self) -> ClientMeta:
        return ClientMeta(name=self.name, password=self.password)

    @property
    def server_address(self) -> Address:
        return Address(hostname=self.server_hostname, port=self.server_port)


@unique
class CBUClientState(CBUStateBase):
    STOPPED = auto()
    STARTING = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    ONLINE = auto()
    STOPPING = auto()


class CBUClient(CBUBase):
    def __init__(self, config: CBUClientConfig):
        super().__init__(config)
        self.config = cast(CBUClientConfig, self.config)
        self._state = CBUClientState.STOPPED

    def _get_logger_name(self):
        return 'Client'

    def _get_main_loop_thread_name(self):
        return 'ClientThread'

    def _main_loop(self):
        try:
            self._connect_and_login()
            self._set_state(CBUClientState.ONLINE)
        except Exception as e:
            self.logger.error('Failed to connect {}: {}'.format(self.config.server_address, e))

    def start(self):
        self.logger.debug('Starting client')
        self._set_state(CBUClientState.STARTING)
        super().start()

    def _is_stopped(self) -> bool:
        return self.in_state(CBUClientState.STOPPED)

    def is_online(self) -> bool:
        return self.in_state(CBUClientState.ONLINE)

    def _connect(self, address: Address):
        self.assert_state(CBUClientState.STARTING)
        self._set_state(CBUClientState.CONNECTING)
        assert self.config.server_address is not None
        self.logger.info('Connecting to {}'.format(self.config.server_address))
        self._sock.connect(address)
        self._set_state(CBUClientState.CONNECTED)

    def _connect_and_login(self):
        self._connect(self.config.server_address)
        self.assert_state(CBUClientState.CONNECTED)
        self.send_packet(LoginPacket(name=self.config.name, password=self.config.password))
        result = self.receive_packet(LoginResultPacket)
        if result.success:
            self.logger.info('Logged in to the server')
        else:
            self.logger.error('Failed to login to the server: {}'.format(result.message))
