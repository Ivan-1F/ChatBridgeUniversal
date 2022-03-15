import click

from chat_bridge_universal.core.server import CBUServer
from chat_bridge_universal.impl.cli.cli_client import CliClient


@click.group()
def cli():
    pass


@cli.command()
@click.argument('config_path')
def server(config_path: str):
    CBUServer(config_path).start()


@cli.command()
@click.argument('config_path')
def client(config_path: str):
    CliClient(config_path).start()


if __name__ == '__main__':
    cli()
