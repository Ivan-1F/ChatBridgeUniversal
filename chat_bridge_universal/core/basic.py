from chat_bridge_universal.common.logger import ChatBridgeUniversalLogger


class ChatBridgeUniversalBase:
    def __init__(self, name: str):
        self.__name = name
        self.logger = ChatBridgeUniversalLogger(self.get_logging_name())

    def get_name(self) -> str:
        return self.__name

    def get_logging_name(self) -> str:
        return self.get_name()
