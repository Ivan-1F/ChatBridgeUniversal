from typing import cast

from mcdreforged.minecraft.rtext import RText, RColor
from mcdreforged.plugin.server_interface import ServerInterface
from mcdreforged.utils.logger import SyncStdoutStreamHandler

from chat_bridge_universal.core.client import CBUClient
from chat_bridge_universal.core.network.protocal import ChatPayload
from chat_bridge_universal.impl.mcdr.config import MCDRClientConfig


class MCDRCBUClient(CBUClient):
    def __init__(self, config: MCDRClientConfig, server: ServerInterface):
        super().__init__(config)
        self.server = server
        self.config = cast(MCDRClientConfig, self.config)
        prev_handler = self.logger.console_handler
        new_handler = SyncStdoutStreamHandler()  # use MCDR's, so the concurrent output won't be messed up
        new_handler.setFormatter(prev_handler.formatter)
        self.logger.removeHandler(prev_handler)
        self.logger.addHandler(new_handler)

    def on_chat(self, sender: str, payload: ChatPayload):
        self.server.say(RText('[{}] {}'.format(sender, payload.formatted_str), RColor.gray))
