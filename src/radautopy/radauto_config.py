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
@click.option('--ftp', 'config_type', flag_value='ftp', help='FTP config')
@click.option('--rclone', 'config_type', flag_value='cloud', help='rclone/cloud config')
@click.option('--http', 'config_type', flag_value='http', help='HTTP(s) config')
@click.argument('config_file', type=click.Path(exists=False))
def create(config_file, config_type):
    defaults = DEFAULT_DIRS | DEFAULT_FILEMAP
    if 'ftp' in config_type:
        config_dict = FTP_CONFIG | defaults
    elif 'cloud' in config_type:
        config_dict = CLOUD_CONFIG | defaults
    elif 'http' in config_type:
        raise NotImplementedError

@create_modify.group()
def modify():
    pass

@create_modify.group()
def validate():
    pass
