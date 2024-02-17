import click
from pathlib import Path
from time import sleep

from .utils.config import LOG_DIR, FTP_CONFIG, CONFIG_DIR, CLOUD_CONFIG, HTTP_CONFIG, SILENCE_CONFIG
from .utils.config.config import ConfigJSON

from .utils.audio import AudioFile
from .utils.ftp import RadFTP
from .utils.cloud import RadCloud
from .utils.mail import RadMail, Attachment
from .utils.log_setup import RadLogger

from .runners.standard import perform_standard
from .runners.news import perform_news

LOG_FILE = Path(LOG_DIR, "radautopy.log")

logger = RadLogger(LOG_FILE).get_logger()

@click.group()
@click.option('-v', '--verbose', is_flag=True, help='enable verbose mode')
@click.argument('config_file')
@click.pass_context
def cli(ctx, config_file, verbose):
    if verbose:
        logger = RadLogger(LOG_FILE, verbose=True).get_logger()

    ctx.ensure_object(dict)

    config = ConfigJSON(config_file)
    ctx.obj['config'] = config
    ctx.obj['mailer'] = RadMail(**config.email)

    job_type = config.job['job_type']
    if 'ftp' in job_type:
        ctx.obj['remote'] = RadFTP(**config.FTP)
    elif 'cloud' in job_type:
        ctx.obj['remote'] = RadCloud(**config.cloud)
    elif 'http' in job_type:
        raise NotImplementedError

@cli.command()
@click.option('-t', '--tries', type=int, default=1, help='define number of tries')
@click.option('-s', '--sleep_timer', type=int, default=1200, help='define number of seconds between tries')
@click.pass_context
def news(ctx, tries, sleep_timer):
    config = ctx.obj.get('config')
    mailer = ctx.obj.get('mailer')
    remote = ctx.obj.get('remote')
    perform_news(config, mailer, remote, tries, sleep_timer)

@cli.command()
@click.pass_context
def standard(ctx):
    config = ctx.obj.get('config')
    mailer = ctx.obj.get('mailer')
    remote = ctx.obj.get('remote')
    perform_standard(config, mailer, remote)

