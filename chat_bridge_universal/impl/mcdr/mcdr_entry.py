import os
from typing import Optional

from mcdreforged.api.decorator import event_listener, new_thread
from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.command_source import CommandSource
from mcdreforged.info_reactor.info import Info
from mcdreforged.minecraft.rtext import RTextBase
from mcdreforged.plugin.server_interface import ServerInterface, PluginServerInterface

from chat_bridge_universal.impl.mcdr.client import MCDRCBUClient, MCDRClientConfig

META = ServerInterface.get_instance().as_plugin_server_interface().get_self_metadata()
PREFIX = '!!cbu'
client: Optional[MCDRCBUClient] = None
config: Optional[MCDRClientConfig] = None


def tr(key: str, *args, **kwargs) -> RTextBase:
    return ServerInterface.get_instance().rtr(META.id + '.' + key, *args, **kwargs)


def display_help(source: CommandSource):
    source.reply(tr('help_message', version=META.version, prefix=PREFIX))


def display_status(source: CommandSource):
    if config is None or client is None:
        source.reply(tr('status.not_init'))
    else:
        source.reply(tr('status.info', client.is_online()))


@new_thread('CBU-restart')
def restart_client(source: CommandSource):
    client.restart()
    source.reply(tr('restarted'))


@new_thread('CBU-unload')
def on_unload(server: PluginServerInterface):
    if client is not None and client.is_running():
        server.logger.info('Stopping CBU client due to plugin unload')
        client.stop()


def register_commands(server: PluginServerInterface):
    server.register_command(
        Literal(PREFIX)
        .runs(display_help)
        .then(Literal('status').runs(display_status))
        .then(Literal('restart').runs(restart_client))
    )


def on_load(server: PluginServerInterface, old_module):
    global config, client
    config_path = os.path.join(server.get_data_folder(), 'config.json')
    config = server.load_config_simple(file_name=config_path, target_class=MCDRClientConfig)
    client = MCDRCBUClient(config, server)

    server.register_help_message(PREFIX, tr('help_summary'))
    client.logger.set_debug_all(config.debug)
    register_commands(server)

    @new_thread('CBU-start')
    def start():
        server.logger.info('Starting CBU client')
        client.start()

    start()


@new_thread('CBU-messenger')
def send_chat(message: str, *, author: str = ''):
    if client is not None:
        if not client.is_running():
            client.start()
        if client.is_online():
            client.send_chat(message, author)


def on_user_info(server: PluginServerInterface, info: Info):
    if info.is_from_server:
        send_chat(info.content, author=info.player)


def on_player_joined(server: PluginServerInterface, player_name: str, info: Info):
    send_chat('{} joined {}'.format(player_name, config.name))


def on_player_left(server: PluginServerInterface, player_name: str):
    send_chat('{} left {}'.format(player_name, config.name))


def on_server_startup(server: PluginServerInterface):
    send_chat('Server has started up')


def on_server_stop(server: PluginServerInterface, return_code: int):
    send_chat('Server stopped')


@event_listener('more_apis.death_message')
def on_player_death(server: PluginServerInterface, message: str):
    send_chat(message)
