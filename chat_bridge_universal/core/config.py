from typing import List

from mcdreforged.utils.serializer import Serializable

from chat_bridge_universal.core.network.basic import Address


class ConfigBase(Serializable):
    aes_key: str = 'ThisIstheSecret'


class ClientMeta(Serializable):
    name: str
    password: str


class ClientConfig(ConfigBase):
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


class ChatBridgeUniversalServerConfig(ConfigBase):
    hostname: str = 'localhost'
    port: int = 30001
    clients: List[ClientMeta] = [
        ClientMeta(name='MyClientName', password='MyClientPassword')
    ]
