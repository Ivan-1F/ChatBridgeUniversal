from chat_bridge_universal.core.basic import ChatBridgeUniversalBase
from chat_bridge_universal.core.config import load_config, ChatBridgeUniversalClientConfig, ClientMeta
from chat_bridge_universal.core.network.basic import NetworkComponent


class ChatBridgeUniversalClient(ChatBridgeUniversalBase, NetworkComponent):
    def __init__(self, config_path: str):
        self.config = load_config(config_path, ChatBridgeUniversalClientConfig)
        super().__init__(name=self.config.client_meta.name)
