import weakref
from logging import Logger, StreamHandler, DEBUG, INFO
from typing import Set

from colorlog import ColoredFormatter


class CBULogger(Logger):
    LOG_COLORS = {
        'DEBUG': 'blue',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
    SECONDARY_LOG_COLORS = {
        'message': {
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red'
        }
    }
    __DEBUG_SWITCH = False
    __REFS: Set['CBULogger'] = weakref.WeakSet()

    @classmethod
    def set_debug_all(cls, value: bool):
        cls.__DEBUG_SWITCH = value
        for logger in cls.__REFS:
            logger.__refresh_debug_level()

    def __init__(self, name: str):
        super().__init__(name)
        self.console_handler = StreamHandler()
        self.console_handler.setFormatter(ColoredFormatter(
            f'[%(name)s] [%(asctime)s] [%(threadName)s/%(log_color)s%(levelname)s%(reset)s]: %(message_log_color)s%(message)s%(reset)s',
            log_colors=self.LOG_COLORS,
            secondary_log_colors=self.SECONDARY_LOG_COLORS,
            datefmt='%H:%M:%S'
        ))
        self.addHandler(self.console_handler)
        self.__REFS.add(self)
        self.__refresh_debug_level()

    def __refresh_debug_level(self):
        self.setLevel(DEBUG if self.__DEBUG_SWITCH else INFO)
