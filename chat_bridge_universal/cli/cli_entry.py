import click

from chat_bridge_universal import constants
from chat_bridge_universal.core.server import CBUServer
from chat_bridge_universal.impl.cli.cli_client import CliClient


@click.group()
def cli():
    pass


@cli.command()
@click.argument('config_path', default='./server_config.json')
def server(config_path: str):
    print('{} v{} server is starting up'.format(constants.NAME, constants.VERSION))
    print('Config file: {}'.format(config_path))
    CBUServer(config_path).start()


@cli.command()
@click.argument('config_path', default='./client_config.json')
def client(config_path: str):
    print('{} v{} cli client is starting up'.format(constants.NAME, constants.VERSION))
    print('Config file: {}'.format(config_path))
    CliClient(config_path).start()
