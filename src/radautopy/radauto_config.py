import click

from .utils import CONFIG_DIR

@click.group()
def create_modify():
    pass

@create_modify.command()
def list_configs():
    try:
        contents = CONFIG_DIR.iterdir()
        for item in contents:
            click.echo(item.name)
    except Exception as e:
        click.echo(f'Error {e}')

@create_modify.group()
def create():
    pass

@create_modify.group()
def modify():
    pass

@create_modify.group()
def validate():
    pass
