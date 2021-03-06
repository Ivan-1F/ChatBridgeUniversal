import json
import socket
import struct
from typing import Type, TypeVar

from chat_bridge_universal.core.network.cryptor import AESCryptor
from chat_bridge_universal.core.network.protocal import AbstractPacket

T = TypeVar('T', bound=AbstractPacket)

RECEIVE_BUFFER_SIZE = 1024


class EmptyContent(socket.error):
    pass


def send_packet(sock: socket.socket, cryptor: AESCryptor, packet: AbstractPacket):
    encrypted_data = cryptor.encrypt(json.dumps(packet.serialize(), ensure_ascii=False))
    packet_data = struct.pack('I', len(encrypted_data)) + encrypted_data
    sock.sendall(packet_data)


def receive_packet(sock: socket.socket, cryptor: AESCryptor, packet_type: Type[T], *, timeout: float = 15) -> T:
    sock.settimeout(timeout)
    header = sock.recv(4)
    if len(header) < 4:
        raise EmptyContent('Empty content received')
    remaining_data_length = struct.unpack('I', header)[0]
    encrypted_data = bytes()
    while remaining_data_length > 0:
        buf = sock.recv(min(remaining_data_length, RECEIVE_BUFFER_SIZE))
        encrypted_data += buf
        remaining_data_length -= len(buf)
    data_str = cryptor.decrypt(encrypted_data)
    try:
        packet = packet_type.deserialize(json.loads(data_str))
        return packet
    except TypeError:
        raise
