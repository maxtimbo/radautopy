import click

from .utils.config import store
from .utils.config.config_modify import ConfigModify
from .utils.config.config_modify import set_cronjob as preform_set_cronjob
from .utils.config.config import ConfigJSON

from .utils.errors import RadautopyError
from .utils.mail import RadMail
from .utils.remote import build_remote


class RadGroup(click.Group):
    def invoke(self, ctx):
        try:
            return super().invoke(ctx)
        except RadautopyError as e:
            raise click.ClickException(str(e)) from e


@click.group(cls=RadGroup)
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
        for name in store.list_names():
            click.echo(name)
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
        if not config.email_exists:
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
        remote = build_remote(config)
        remote.validate()

