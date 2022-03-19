import socket
from threading import Thread, current_thread
from typing import Callable, Optional, NamedTuple, Collection, Union

from chat_bridge_universal.core.config import CBUConfigBase
from chat_bridge_universal.core.state import CBUStateBase
from chat_bridge_universal.utils.logger import CBULogger


class Address(NamedTuple):
    hostname: str
    port: int

    def __str__(self):
        return '{}:{}'.format(self.hostname, self.port)


class CBUBase:
    def __init__(self, config: CBUConfigBase):
        self.logger = CBULogger(self._get_logger_name())
        self.config = config
        self._state: CBUStateBase
        self.__main_thread: Optional[Thread] = None
        self._sock: socket.socket = socket.socket()

    def _get_logger_name(self):
        return self.__class__.__name__

    def _get_main_loop_thread_name(self):
        return self.__class__.__name__ + 'Thread'

    def in_state(self, state: Union[CBUStateBase, Collection[CBUStateBase]]):
        return self._state.in_state(state)

    def _set_state(self, state: CBUStateBase):
        self._state = state

    def assert_state(self, state: Union[CBUStateBase, Collection[CBUStateBase]]):
        if not self.in_state(state):
            raise AssertionError('Excepted status {} but {} found'.format(state, self._state))

    def _start_thread(self, target: Callable, name: str, *args):
        thread = Thread(target=target, name=name, args=args, daemon=True)
        thread.start()
        self.logger.debug('Started new thread {}: {}'.format(name, thread))
        return thread

    def _main_loop(self):
        pass

    def start(self):
        def func():
            if self.__main_thread is not None:
                raise RuntimeError('Already running')
            self._main_loop()
        self.__main_thread = self._start_thread(target=func, name=self._get_main_loop_thread_name())

    def stop(self):
        """
        Stop the client/server, and wait until the MainLoop thread exits
        Need to be called on a non-MainLoop thread
        """
        self.logger.info('Stopping')
        self._stop()
        self.logger.debug('Joining MainLoop thread')
        thread = self.__main_thread
        if thread is not None:
            if thread is not current_thread():
                thread.join()
            else:
                self.logger.warning('Joining current thread {}'.format(thread))
        self.logger.debug('Joined MainLoop thread')

    def _stop(self):
        """
        Internal clean up
        """
        self._sock.close()
