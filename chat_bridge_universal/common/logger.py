from logging import Logger, LogRecord, StreamHandler

from colorlog import ColoredFormatter


class ConsoleHandler(StreamHandler):
    def emit(self, record: LogRecord) -> None:
        super().emit(record)


class ChatBridgeUniversalLogger(Logger):
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

    def __init__(self, name: str):
        super().__init__(name)
        self.console_handler = ConsoleHandler()
        self.console_handler.setFormatter(ColoredFormatter(
            f'[%(name)s] [%(asctime)s] [%(threadName)s/%(log_color)s%(levelname)s%(reset)s]: %(message_log_color)s%(message)s%(reset)s',
            log_colors=self.LOG_COLORS,
            secondary_log_colors=self.SECONDARY_LOG_COLORS,
            datefmt='%H:%M:%S'
        ))
        self.addHandler(self.console_handler)
