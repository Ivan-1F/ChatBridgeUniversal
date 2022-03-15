import json
import os
from typing import List, TypeVar, Type, NamedTuple

from mcdreforged.utils.serializer import Serializable


class Address(NamedTuple):
    hostname: str
    port: int

    def __str__(self):
        return '{}:{}'.format(self.hostname, self.port)


class ConfigBase(Serializable):
    aes_key: str = 'ThisIstheSecret'


class ClientMeta(Serializable):
    name: str
    password: str


class CBUClientConfig(ConfigBase):
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


class CBUServerConfig(ConfigBase):
    hostname: str = 'localhost'
    port: int = 30001
    clients: List[ClientMeta] = [
        ClientMeta(name='MyClientName', password='MyClientPassword')
    ]

    @property
    def address(self) -> Address:
        return Address(hostname=self.hostname, port=self.port)


T = TypeVar('T', ConfigBase, ConfigBase)
