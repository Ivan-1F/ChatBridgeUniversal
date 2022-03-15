import json
import os
from threading import Thread, current_thread
from typing import TypeVar, Generic, Callable, Optional, cast, Type, List

from chat_bridge_universal.common.logger import CBULogger
from chat_bridge_universal.core.config import ConfigBase, CBUServerConfig

T = TypeVar('T', ConfigBase, ConfigBase)


class CBUBase:
    def __init__(self, config_path: str, config_class: Type[T]):
        self.logger = CBULogger(self.get_logger_name())
        self.config = self.load_config(config_path, config_class)
        self.__main_thread: Optional[Thread] = None

    def load_config(self, config_path: str, config_class: Type[T]) -> T:
        config = config_class.get_default()
        if not os.path.isfile(config_path):
            self.logger.warning('Configure file not found!'.format(config_path))
            with open(config_path, 'w', encoding='utf8') as file:
                json.dump(config.serialize(), file, ensure_ascii=False, indent=4)
            self.logger.info('Default example configure generated'.format(config_path))
            return self.load_config(config_path, config_class)
        else:
            with open(config_path, encoding='utf8') as file:
                config.update_from(json.load(file))
            with open(config_path, 'w', encoding='utf8') as file:
                json.dump(config.serialize(), file, ensure_ascii=False, indent=4)
            return config

    def get_logger_name(self) -> str:
        pass

    def get_main_thread_name(self) -> str:
        pass

    def _start_thread(self, target: Callable, name: str):
        thread = Thread(target=target, args=(), name=name, daemon=True)
        thread.start()
        self.logger.debug('Started thread {}: {}'.format(name, thread))
        return thread

    def _main_loop(self):
        pass

    def start(self):
        def func():
            self._main_loop()
        self.__main_thread = self._start_thread(func, self.get_main_thread_name())

    def stop(self):
        """
        Stop the client/server, and wait until the MainLoop thread exits
        Need to be called on a non-MainLoop thread
        """
        self.logger.debug('Joining MainLoop thread')
        # with self.__thread_run_lock:
        thread = self.__main_thread
        if thread is not None:
            if thread is not current_thread():
                thread.join()
            else:
                self.logger.warning('Joining current thread {}'.format(thread))
        self.logger.debug('Joined MainLoop thread')
