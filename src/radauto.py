#!/usr/bin/python3

import argparse
import click
from pathlib import Path
from time import sleep

from utils import LOG_DIR, FTP_CONFIG
from utils.audio import AudioFile
from utils.config import ConfigJSON
from utils.ftp import RadFTP
from utils.mail import RadMail, Attachment
from utils.log_setup import RadLogger

LOG_FILE = Path(LOG_DIR, "radautopy.log")

logger = RadLogger(LOG_FILE).get_logger()

@click.group()
@click.option('-v', '--verbose', is_flag=True, help='enable verbose mode')
@click.option('--ftp', is_flag=True, help='run as FTP')
@click.option('--rclone', is_flag=True, help='run as rclone/cloud')
@click.option('--http', is_flag=True, help='run as http(s)')
@click.argument('config_file', type=click.Path(exists=False))
@click.pass_context
def cli(ctx, verbose, config_file, ftp, rclone, http):
    """
    RadioAutoPy command line tool.
    Please supply a config file.
    You can specify verbose to output to stdout.
    """
    if verbose:
        logger = RadLogger(LOG_FILE, verbose=True).get_logger()

    if ftp:
        config = ConfigJSON(config_file, FTP_CONFIG)
        ctx.obj['config'] = config
    elif rclone:
        pass
    elif http:
        pass

@cli.command()
@click.pass_context
def edit(ctx):
    config = ctx.obj.get('config')
    print(config.email)


@cli.group()
def validate():
    """
    Validate config file.
    """
    print(cli.config_file)
    click.echo('validate')

@validate.command()
def email():
    """
    Validate email settings.
    A test email will be sent upon success.
    """
    click.echo('validate email')

@validate.command()
def remote():
    """
    Validate remote settings.
    A list of contents of the remote destination will be supplied upon success.
    """
    click.echo('validate remote')

#@cli.group()
#def run():
#    """
#    Use `rclone`, `http`, or `ftp` to run the supplied config file
#    """
#    click.echo('run')
#
#@run.command()
#def rclone():
#    click.echo('rclone')
#
#@run.command()
#def http():
#    click.echo('http')
#
#@run.command()
#@click.option('--news', is_flag=False, help='use news runner')
#def ftp(news):
#    if news:
#        click.echo('news')
#    else:
#        click.echo('standard')

if __name__ == '__main__':
    cli()
