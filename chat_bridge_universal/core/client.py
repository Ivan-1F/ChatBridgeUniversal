from enum import auto, unique
from typing import cast

from chat_bridge_universal.core.basic import CBUBase, Address
from chat_bridge_universal.core.config import CBUConfigBase, ClientMeta
from chat_bridge_universal.core.state import CBUStateBase


class CBUClientConfig(CBUConfigBase):
    name: str = 'MyClientName'
    password: str = 'MyClientPassword'
    server_hostname: str = '127.0.0.1'
    server_port: int = 30001

    @property
    def client_info(self) -> ClientMeta:
        return ClientMeta(name=self.name, password=self.password)

    @property
    def server_address(self) -> Address:
        return Address(hostname=self.server_hostname, port=self.server_port)


@unique
class CBUClientState(CBUStateBase):
    STOPPED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    ONLINE = auto()
    STOPPING = auto()


class CBUClient(CBUBase):
    def __init__(self, config: CBUClientConfig):
        super().__init__(config)
        self.config = cast(CBUClientConfig, self.config)
        self.state = CBUClientState.STOPPED

    def _get_logger_name(self):
        return 'Client'

    def _get_main_loop_thread_name(self):
        return 'ClientThread'

    def _main_loop(self):
        pass

    def _connect(self, address: Address):
        self._sock.connect(address)
