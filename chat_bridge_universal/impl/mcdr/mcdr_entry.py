import os
from threading import Lock, Event
from typing import Optional

from mcdreforged.api.decorator import new_thread, event_listener
from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.command_source import CommandSource
from mcdreforged.info_reactor.info import Info
from mcdreforged.minecraft.rtext import RTextBase
from mcdreforged.plugin.server_interface import ServerInterface, PluginServerInterface

from chat_bridge_universal.impl.mcdr.mcdr_client import CBUMCDRClient, MCDRClientConfig

META = ServerInterface.get_instance().as_plugin_server_interface().get_self_metadata()
PREFIX = '!!cbu'

client: Optional[CBUMCDRClient] = None
config: Optional[MCDRClientConfig] = None
plugin_unload_flag = False
cb_lock = Lock()
cb_stop_done = Event()


def tr(key: str, *args, **kwargs) -> RTextBase:
    return ServerInterface.get_instance().rtr(META.id + '.' + key, *args, **kwargs)


def display_help(source: CommandSource):
    source.reply(tr('help_message', name=META.name, version=META.version, prefix=PREFIX))


def display_status(source: CommandSource):
    if config is None or client is None:
        source.reply(tr('status.not_init'))
    else:
        source.reply(tr('status.info', client.is_online()))


@new_thread('ChatBridgeUniversal-restart')
def restart_client(source: CommandSource):
    with cb_lock:
        client.restart()
    source.reply(tr('restarted'))


def load_or_generate_config(server: PluginServerInterface):
    config_path = os.path.join(server.get_data_folder(), 'config.json')
    if not os.path.isfile(config_path):
        server.logger.exception('Config file not found! ChatBridge will not work properly')
        server.logger.error('Fill the default configure file with correct values and reload the plugin')
        server.save_config_simple(MCDRClientConfig.get_default())
        return

    global config
    config = server.load_config_simple(config_path, target_class=MCDRClientConfig)


def register_commands(server: PluginServerInterface):
    server.register_help_message(PREFIX, tr('help_summary'))
    server.register_command(
        Literal(PREFIX)
        .runs(display_help)
        .then(Literal('status').runs(display_status))
        .then(Literal('restart').runs(restart_client))
    )


@new_thread('ChatBridgeUniversal-unload')
def on_unload(server: PluginServerInterface):
    global plugin_unload_flag
    plugin_unload_flag = True
    with cb_lock:
        if client is not None and not client.is_stopped():
            server.logger.info('Stopping CBU client due to plugin unload')
            client.stop()
    cb_stop_done.set()


@new_thread('ChatBridgeUniversal-messenger')
def send_chat(message: str, *, author: str = ''):
    with cb_lock:
        if client is not None:
            if client.is_stopped():
                client.start()
            if client.is_online():
                client.send_chat(message, author)


def on_load(server: PluginServerInterface, old_module):
    load_or_generate_config(server)

    global client
    client = CBUMCDRClient(config, server)

    register_commands(server)

    @new_thread('ChatBridgeUniversal-start')
    def start():
        with cb_lock:
            if isinstance(getattr(old_module, 'cb_stop_done', None), type(cb_stop_done)):
                stop_event: Event = old_module.cb_stop_done
                if not stop_event.wait(30):
                    server.logger.warning('Previous CBU instance does not stop for 30s')
            server.logger.info('Starting CBU client')
            client.start()

    start()


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

