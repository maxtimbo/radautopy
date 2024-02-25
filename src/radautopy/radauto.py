import click
from pathlib import Path
from time import sleep

from .utils.config import LOG_DIR
from .utils.config.config import ConfigJSON

from .utils.audio import AudioFile
from .utils.ftp import RadFTP
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
@click.option('-v', '--verbose', is_flag=True, help='enable verbose mode')
@click.option('--disable_email', is_flag=True, help='disable email notification', default=True)
@click.argument('config_file')
@click.pass_context
def cli(ctx, config_file, verbose, disable_email):
    if verbose:
        logger = RadLogger(LOG_FILE, verbose=True).get_logger()

    ctx.ensure_object(dict)

    config = ConfigJSON(config_file)
    ctx.obj['config'] = config
    ctx.obj['mailer'] = RadMail(**config.email)
    ctx.obj['email_bool'] = disable_email

    job_type = config.job['job_type']
    if 'ftp' in job_type:
        ctx.obj['remote'] = RadFTP(**config.FTP)
    elif 'cloud' in job_type:
        ctx.obj['remote'] = RadCloud(**config.cloud)
    elif 'rss' in job_type:
        ctx.obj['remote'] = RadRSS(**config.rss)
    elif 'ttwn' in job_type:
        ctx.obj['remote'] = TTWN(**config.ttwn, timestamp_dir = config.dirs['audio_tmp'])

@cli.command()
@click.option('-t', '--tries', type=int, default=1, help='define number of tries')
@click.option('-s', '--sleep_timer', type=int, default=1200, help='define number of seconds between tries')
@click.pass_context
def news(ctx, tries, sleep_timer):
    perform_news(ctx.obj.get('config'), ctx.obj.get('mailer'), ctx.obj.get('email_bool'), ctx.obj.get('remote'), tries, sleep_timer)

@cli.command()
@click.pass_context
def standard(ctx):
    perform_standard(ctx.obj.get('config'), ctx.obj.get('mailer'), ctx.obj.get('email_bool'), ctx.obj.get('remote'))

@cli.command()
@click.option('-t', '--threshold', type=int, default = -60, help='define db threshold for silence split')
@click.option('-d', '--duration', type=int, default = 15, help='silence duration in seconds')
@click.pass_context
def split_single(ctx, threshold, duration):
    perform_split_single(ctx.obj.get('config'), ctx.obj.get('mailer'), ctx.obj.get('email_bool'), ctx.obj.get('remote'), threshold, duration)

@cli.command()
@click.pass_context
def ttwn(ctx):
    perform_ttwn(ctx.obj.get('config'), ctx.obj.get('mailer'), ctx.obj.get('email_bool'), ctx.obj.get('remote'))

