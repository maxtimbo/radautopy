import click

from .utils.config import CONFIG_DIR
from .utils.config.config_modify import ConfigModify
from .utils.config.config_modify import set_cronjob as preform_set_cronjob
from .utils.config.config import ConfigJSON

from .utils.cloud import RadCloud
from .utils.ftp import RadFTP
from .utils.sftp import RadSFTP
from .utils.mail import RadMail
from .utils.rss import RadRSS
from .utils.ttwn import TTWN

@click.group()
def create_modify():
    """
    Create, modify, or validate config files for radautopy
    """
    pass

@create_modify.command()
def list_configs():
    """
    Returns the list of available configs
    """
    try:
        contents = CONFIG_DIR.iterdir()
        for item in contents:
            click.echo(item.name)
    except Exception as e:
        click.echo(f'Error {e}')

@create_modify.command()
@click.option('--ftp', 'config_type', flag_value='ftp', help='FTP config')
@click.option('--sftp', 'config_type', flag_value='sftp', help='SFTP config')
@click.option('--rclone', 'config_type', flag_value='cloud', help='rclone/cloud config')
@click.option('--rss', 'config_type', flag_value='rss', help='rss config')
@click.option('--ttwn', 'config_type', flag_value='ttwn', help='TTWN Config')
@click.argument('config_file', type=click.Path(exists=False))
def create(config_type, config_file):
    """
    Create a config file
    """
    if not config_type:
        click.echo('\n > A job type must be specified\n')
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit()
    else:
        config = ConfigModify(config_type, config_file)
        if not config.email_config.exists():
            config.set_email()

        config.set_config()


@create_modify.command()
@click.argument('config_file', required=False)
def modify(config_file):
    """
    Modify an existing CONFIG_FILE or none to modify global email config
    """
    if config_file is None:
        email = ConfigJSON()
        config = ConfigModify()
        config.set_email(email.email_dict)
    else:
        config = ConfigJSON(config_file)
        modify = ConfigModify(config_file = config.config_file)
        modify.set_config(config.config_dict)

@create_modify.command()
@click.argument('config_file')
def set_cronjob(config_file):
    """
    Set cronjob for an existing config
    """
    config = ConfigJSON(config_file)
    preform_set_cronjob(config.job, config_file)



@create_modify.command()
@click.argument('config_file', required=False)
def validate(config_file):
    """
    Validate an existing config
    """
    if config_file is None:
        email = ConfigJSON()
        mailer = RadMail(**email.email)
        mailer.validate()
    else:
        config = ConfigJSON(config_file)
        if 'ftp' == config.job['job_type']:
            remote = RadFTP(**config.FTP)
        elif 'sftp' == config.job['job_type']:
            remote = RadSFTP(**config.SFTP)
        elif 'cloud' == config.job['job_type']:
            remote = RadCloud(**config.cloud)
        elif 'rss' == config.job['job_type']:
            remote = RadRSS(**config.rss)
        elif 'ttwn' == config.job['job_type']:
            remote = TTWN(**config.ttwn, timestamp_dir = config.dirs['audio_tmp'])

        remote.validate()

