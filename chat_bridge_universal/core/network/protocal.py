from mcdreforged.utils.serializer import Serializable


class AbstractPayload(Serializable):
    pass


class ChatPayload(AbstractPayload):
    author: str
    message: str


class AbstractPacket(Serializable):
    pass


class LoginPacket(AbstractPacket):
    name: str
    password: str


class LoginResultPacket(AbstractPacket):
    success: bool
    message: str


class ChatPacket(AbstractPacket):
    sender: str
    payload: ChatPayload

