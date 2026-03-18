import click
from pathlib import Path
from importlib.metadata import version

from .utils.config import LOG_DIR
from .utils.config.config import ConfigJSON

from .utils.audio import AudioFile
from .utils.ftp import RadFTP
from .utils.sftp import RadSFTP
from .utils.cloud import RadCloud
from .utils.rss import RadRSS
from .utils.ttwn import TTWN
from .utils.mail import RadMail
from .utils.log_setup import RadLogger

from .runners.standard import perform_standard
from .runners.news import perform_news
from .runners.split_single import perform_split_single
from .runners.ttwn import perform_ttwn

LOG_FILE = Path(LOG_DIR, "radautopy.log")

logger = RadLogger(LOG_FILE).get_logger()

@click.group()
@click.version_option(version = version("radautopy"), prog_name = "radautopy")
@click.option('-v', '--verbose', is_flag=True, help='enable verbose mode')
@click.option('--disable_email', is_flag=True, help='disable email notification', default=False)
@click.argument('config_file')
@click.pass_context
def cli(ctx: click.Context, config_file: str, verbose: bool, disable_email:bool) -> None:
    if verbose:
        logger = RadLogger(LOG_FILE, verbose=True).get_logger()

    ctx.ensure_object(dict)

    config = ConfigJSON(config_file)
    ctx.obj['config'] = config
    ctx.obj['mailer'] = RadMail(**config.email)
    ctx.obj['email_bool'] = disable_email

    job_type = config.job['job_type']
    if 'ftp' == job_type:
        ctx.obj['remote'] = RadFTP(**config.FTP)
    elif 'sftp' == job_type:
        ctx.obj['remote'] = RadSFTP(**config.SFTP)
    elif 'cloud' == job_type:
        ctx.obj['remote'] = RadCloud(**config.cloud)
    elif 'rss' == job_type:
        ctx.obj['remote'] = RadRSS(**config.rss)
    elif 'ttwn' == job_type:
        ctx.obj['remote'] = TTWN(**config.ttwn)

@cli.command()
@click.option('-t', '--tries', type=int, default=1, help='define number of tries')
@click.option('-s', '--sleep_timer', type=int, default=1200, help='define number of seconds between tries')
@click.pass_context
def news(ctx: click.Context, tries: int, sleep_timer: int) -> None:
    perform_news(ctx.obj.get('config'), ctx.obj.get('mailer'), ctx.obj.get('email_bool'), ctx.obj.get('remote'), tries, sleep_timer)

@cli.command()
@click.pass_context
def standard(ctx: click.Context) -> None:
    perform_standard(ctx.obj.get('config'), ctx.obj.get('mailer'), ctx.obj.get('email_bool'), ctx.obj.get('remote'))

@cli.command()
@click.option('-t', '--threshold', type=int, default = -60, help='define db threshold for silence split')
@click.option('-d', '--duration', type=int, default = 15, help='silence duration in seconds')
@click.pass_context
def split_single(ctx: click.Context, threshold: int, duration: int) -> None:
    perform_split_single(ctx.obj.get('config'), ctx.obj.get('mailer'), ctx.obj.get('email_bool'), ctx.obj.get('remote'), threshold, duration)

@cli.command()
@click.pass_context
def ttwn(ctx: click.Context) -> None:
    perform_ttwn(ctx.obj.get('config'), ctx.obj.get('mailer'), ctx.obj.get('email_bool'), ctx.obj.get('remote'))

