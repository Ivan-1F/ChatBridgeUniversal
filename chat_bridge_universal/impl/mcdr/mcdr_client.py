from typing import cast

from mcdreforged.minecraft.rtext import RText, RColor
from mcdreforged.plugin.server_interface import ServerInterface
from mcdreforged.utils.logger import SyncStdoutStreamHandler

from chat_bridge_universal.core.client import CBUClient
from chat_bridge_universal.core.config import CBUClientConfig
from chat_bridge_universal.core.network.protocal import ChatPayload


class MCDRClientConfig(CBUClientConfig):
    pass


class MCDRClient(CBUClient):
    def __init__(self, config: MCDRClientConfig, server: ServerInterface):
        super().__init__(config)
        self.config = cast(MCDRClientConfig, self.config)
        self.server = server
        prev_handler = self.logger.console_handler
        new_handler = SyncStdoutStreamHandler()  # use MCDR's, so the concurrent output won't be messed up
        new_handler.setFormatter(prev_handler.formatter)
        self.logger.removeHandler(prev_handler)
        self.logger.addHandler(new_handler)

    def get_logger_name(self) -> str:
        return 'ChatBridgeUniversal@{}'.format(hex((id(self) >> 16) & (id(self) & 0xFFFF))[2:].rjust(4, '0'))

    def get_main_thread_name(self) -> str:
        return 'ChatBridgeUniversal-' + super().get_main_thread_name()

    def on_chat(self, sender: str, payload: ChatPayload):
        self.server.say(RText('[{}] {}'.format(sender, payload.formatted_str), RColor.gray))
