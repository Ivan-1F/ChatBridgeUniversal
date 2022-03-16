from typing import List

from mcdreforged.utils.serializer import Serializable


class AbstractPacket(Serializable):
    pass


class LoginPacket(AbstractPacket):
    name: str
    password: str


class LoginResultPacket(AbstractPacket):
    success: bool


class ChatPacket(AbstractPacket):
    sender: str
    receivers: List[str]
    broadcast: bool
    payload: dict
