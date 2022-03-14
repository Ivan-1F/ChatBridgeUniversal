from chat_bridge_universal.core.basic import ChatBridgeUniversalBase
from chat_bridge_universal.core.config import ChatBridgeUniversalServerConfig, load_config
from chat_bridge_universal.core.network.basic import NetworkComponent


class ChatBridgeUniversalServer(ChatBridgeUniversalBase, NetworkComponent):
    def __init__(self, config_path: str):
        super().__init__('Server')
        self.config = load_config(config_path, ChatBridgeUniversalServerConfig)

