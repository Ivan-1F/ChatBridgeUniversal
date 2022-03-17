import json
import socket
import struct

__all__ = [
	'send_packet',
	'receive_data',
	'EmptyContent',
]

from typing import TypeVar, Type

from chat_bridge_universal.core.network.cryptor import AESCryptor
from chat_bridge_universal.core.network.protocal import AbstractPacket

RECEIVE_BUFFER_SIZE = 1024


class EmptyContent(socket.error):
	pass


def send_packet(sock: socket.socket, cryptor: AESCryptor, packet: AbstractPacket):
	encrypted_data = cryptor.encrypt(json.dumps(packet.serialize(), ensure_ascii=False))
	packet_data = struct.pack('I', len(encrypted_data)) + encrypted_data
	sock.sendall(packet_data)


def receive_data(sock: socket.socket, cryptor: AESCryptor, *, timeout: float) -> str:
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
	return cryptor.decrypt(encrypted_data)


T = TypeVar('T', bound=AbstractPacket)


def receive_packet(sock: socket.socket, cryptor: AESCryptor, packet_type: Type[T], *, timeout: float) -> T:
	if sock is None:
		sock = sock
	data_string = receive_data(sock, cryptor, timeout=timeout)
	try:
		data = json.loads(data_string)
	except ValueError:
		raise('Fail to decode received string: {}'.format(data_string))

	try:
		packet = packet_type.deserialize(data)
	except Exception:
		raise('Fail to deserialize received json to {}: {}'.format(packet_type, data))
	return packet
