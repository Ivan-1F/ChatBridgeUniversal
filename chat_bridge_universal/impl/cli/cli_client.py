from chat_bridge_universal.core.client import CBUClient, CBUClientConfig
from chat_bridge_universal.core.config import load_config


class CliClient(CBUClient):
    def __init__(self, config_path: str):
        super().__init__(load_config(config_path, CBUClientConfig))

    def console_loop(self):
        while not self._is_stopped():
            input_ = input()
            if input_ == 'stop':
                self.stop()

    def start(self):
        super().start()
        self.console_loop()
