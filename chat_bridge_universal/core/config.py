import json
import os
from typing import List, TypeVar, Generic, Type

from mcdreforged.utils.serializer import Serializable

from chat_bridge_universal.core.network.basic import Address


class ConfigBase(Serializable):
    aes_key: str = 'ThisIstheSecret'


class ClientMeta(Serializable):
    name: str
    password: str


class ChatBridgeUniversalClientConfig(ConfigBase):
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


class ChatBridgeUniversalServerConfig(ConfigBase):
    hostname: str = 'localhost'
    port: int = 30001
    clients: List[ClientMeta] = [
        ClientMeta(name='MyClientName', password='MyClientPassword')
    ]

    @property
    def address(self) -> Address:
        return Address(hostname=self.hostname, port=self.port)


T = TypeVar('T', ConfigBase, ConfigBase)


def load_config(config_path: str, config_class: Type[T]) -> T:
    config = config_class.get_default()
    if not os.path.isfile(config_path):
        print('Configure file not found!'.format(config_path))
        with open(config_path, 'w', encoding='utf8') as file:
            json.dump(config.serialize(), file, ensure_ascii=False, indent=4)
        print('Default example configure generated'.format(config_path))
        return load_config(config_path, config_class)
    else:
        with open(config_path, encoding='utf8') as file:
            config.update_from(json.load(file))
        with open(config_path, 'w', encoding='utf8') as file:
            json.dump(config.serialize(), file, ensure_ascii=False, indent=4)
        return config
