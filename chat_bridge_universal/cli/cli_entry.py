import click

from chat_bridge_universal import constants
from chat_bridge_universal.core.server import CBUServer


@click.group()
def cli():
    pass


@cli.command()
@click.argument('config_path')
def server(config_path):
    print('{} v{} server is starting up'.format(constants.NAME, constants.VERSION))
    CBUServer(config_path).start()
