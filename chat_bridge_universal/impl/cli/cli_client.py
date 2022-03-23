from chat_bridge_universal.core.client import CBUClient, CBUClientConfig
from chat_bridge_universal.core.config import load_config
from chat_bridge_universal.core.network.protocal import ChatPayload


class CliClient(CBUClient):
    def __init__(self, config_path: str):
        super().__init__(load_config(config_path, CBUClientConfig))

    def console_loop(self):
        while not self._is_stopped():
            input_ = input()
            if input_ == 'stop':
                self.stop()
            else:
                self.send_chat(input_)

    def on_chat(self, sender: str, payload: ChatPayload):
        self.logger.info('Received chat from {}: {}'.format(sender, payload.formatted_str))

    def start(self):
        super().start()
        self.console_loop()
