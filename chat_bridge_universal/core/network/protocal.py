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


class AbstractPayload(Serializable):
    pass


class ChatPayload(AbstractPayload):
    author: str
    message: str

    @property
    def formatted_str(self) -> str:
        if self.author != '':
            return '<{}> {}'.format(self.author, self.message)
        else:
            return self.message
