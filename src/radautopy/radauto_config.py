import click

from .utils.config_modify import ConfigModify

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
@click.option('--ftp', 'config_type', flag_value='ftp', help='FTP config')
@click.option('--rclone', 'config_type', flag_value='cloud', help='rclone/cloud config')
@click.option('--http', 'config_type', flag_value='http', help='HTTP(s) config')
@click.argument('config_file', type=click.Path(exists=False))
def create(config_type, config_file):
    config = ConfigModify(config_type, config_file)
    if not config.email_config.exists():
        config.set_email()

    config.set_config()


@create_modify.group()
def modify():
    pass

@create_modify.group()
def validate():
    pass
