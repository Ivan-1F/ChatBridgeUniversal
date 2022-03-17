from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter

from chat_bridge_universal.core.client import CBUClient


class CliClient(CBUClient):
    def __init__(self, config_path: str):
        super().__init__(config_path)
        completer = WordCompleter(['stop', 'send', 'list', 'help'])
        self.__prompt_session = PromptSession(completer=completer)

    def prompt_loop(self):
        while not self.is_stopped():
            text = self.__prompt_session.prompt('> ')
            self.logger.info('Handling user input: {}'.format(text))
            if text == 'stop':
                self.stop()
            else:
                self.send_chat(text)

    def start(self):
        super().start()
        self.prompt_loop()
