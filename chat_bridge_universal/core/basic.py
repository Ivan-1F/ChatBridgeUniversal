import json
import os
import socket
from enum import Enum, unique
from threading import Thread, current_thread, RLock
from typing import TypeVar, Callable, Optional, Type, Iterable, Union

from chat_bridge_universal.common.logger import CBULogger
from chat_bridge_universal.core.config import ConfigBase
from chat_bridge_universal.core.network import net_util
from chat_bridge_universal.core.network.cryptor import AESCryptor
from chat_bridge_universal.core.network.protocal import AbstractPacket


@unique
class StateBase(Enum):
    def in_state(self, states):
        if type(states) is type(self):
            return self is states
        elif not isinstance(states, Iterable):
            states = (states,)
        return self in states


T = TypeVar('T', bound=ConfigBase)


class CBUBase:
    """
    Base class for all the ChatBridgeUniversal components
    """

    def __init__(self, aes: Union[str, AESCryptor]):
        self.logger = CBULogger(self.get_logger_name())
        self.__main_thread: Optional[Thread] = None
        self.__thread_run_lock = RLock()
        self._sock: Optional[socket.socket] = None
        self._state: StateBase
        if isinstance(aes, AESCryptor):
            self._cryptor = aes
        else:
            self._cryptor = AESCryptor(aes)

    def get_logger_name(self) -> str:
        pass

    def get_main_thread_name(self) -> str:
        pass

    def _send_packet(self, packet: AbstractPacket):
        net_util.send_packet(self._sock, self._cryptor, packet)

    PT = TypeVar('PT', bound=AbstractPacket)

    def _receive_packet(self, packet_type: Type[PT]) -> PT:
        packet = net_util.receive_packet(self._sock, self._cryptor, packet_type, timeout=15)
        return packet

    def _start_thread(self, target: Callable, name: str):
        thread = Thread(target=target, args=(), name=name, daemon=True)
        thread.start()
        self.logger.debug('Started thread {}: {}'.format(name, thread))
        return thread

    def in_state(self, state) -> bool:
        return self._state.in_state(state)

    def _set_state(self, state):
        self._state = state

    def assert_state(self, state):
        if not self.in_state(state):
            raise AssertionError('Excepted state {} but {} found'.format(state, self._state))

    def _main_loop(self):
        pass

    def start(self):
        """
        Start the client/server mainloop in a new thread (self.__main_thread)
        """

        def func():
            self._main_loop()
            with self.__thread_run_lock:
                self.__thread_run = None

        with self.__thread_run_lock:
            if self.__main_thread is not None:
                raise RuntimeError('Already running')
        self.__main_thread = self._start_thread(func, self.get_main_thread_name())

    def stop(self):
        """
        Stop the client/server, and wait until the MainLoop thread exits
        Need to be called on a non-MainLoop thread
        """
        self.logger.debug('Joining MainLoop thread')
        with self.__thread_run_lock:
            thread = self.__main_thread
        if thread is not None:
            if thread is not current_thread():
                thread.join()
            else:
                self.logger.warning('Joining current thread {}'.format(thread))
        self.logger.debug('Joined MainLoop thread')


class Configurable:
    def __init__(self, config_path: str, config_class: Type[T]):
        self.config = self.load_config(config_path, config_class)

    def load_config(self, config_path: str, config_class: Type[T]) -> T:
        config = config_class.get_default()
        if not os.path.isfile(config_path):
            self.get_logger().warning('Configure file not found!'.format(config_path))
            with open(config_path, 'w', encoding='utf8') as file:
                json.dump(config.serialize(), file, ensure_ascii=False, indent=4)
            self.get_logger().info('Default example configure generated'.format(config_path))
            return self.load_config(config_path, config_class)
        else:
            with open(config_path, encoding='utf8') as file:
                config.update_from(json.load(file))
            with open(config_path, 'w', encoding='utf8') as file:
                json.dump(config.serialize(), file, ensure_ascii=False, indent=4)
            return config

    def get_logger(self) -> CBULogger:
        pass
