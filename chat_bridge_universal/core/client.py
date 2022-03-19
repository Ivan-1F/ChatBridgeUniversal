from enum import auto, unique

from chat_bridge_universal.core.basic import CBUBase
from chat_bridge_universal.core.config import CBUConfigBase
from chat_bridge_universal.core.state import CBUStateBase


class CBUClientConfig(CBUConfigBase):
    pass


@unique
class CBUClientState(CBUStateBase):
    STOPPED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    ONLINE = auto()
    STOPPING = auto()


class CBUClient(CBUBase):
    def __init__(self, config: CBUConfigBase):
        super().__init__(config)
        self.state = CBUClientState.STOPPED

    def _get_logger_name(self):
        return 'Client'

    def _get_main_loop_thread_name(self):
        return 'ClientThread'

    def _main_loop(self):
        pass
