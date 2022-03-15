import click

from chat_bridge_universal.core.client import CBUClient
from chat_bridge_universal.core.server import CBUServer


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
    CBUClient(config_path).start()


if __name__ == '__main__':
    cli()
