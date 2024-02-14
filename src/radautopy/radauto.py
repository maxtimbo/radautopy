<<<<<<< HEAD
import argparse
=======
>>>>>>> 24598825c3358d629b1032ca79fdbdd0079a4d4d
import click
from pathlib import Path
from time import sleep

from .utils import LOG_DIR, FTP_CONFIG, CONFIG_DIR, CLOUD_CONFIG, HTTP_CONFIG, SILENCE_CONFIG
from .utils.audio import AudioFile
from .utils.config import ConfigJSON
from .utils.ftp import RadFTP
from .utils.cloud import RadCloud
from .utils.mail import RadMail, Attachment
from .utils.log_setup import RadLogger

LOG_FILE = Path(LOG_DIR, "radautopy.log")

logger = RadLogger(LOG_FILE).get_logger()

def perform_standard(config, mailer, remote):
    config.concat_directories_filemap()
    downloads = [(x['input_file'].name, x['input_file']) for x in config.filemap]
    try:
        remote.download_files(downloads)
        for i, o in downloads:
            mailer.append_table_data('downloaded', i)
    except:
        mailer.p('Download unsuccessful')
    for track in config.filemap:
        audio = AudioFile(track['input_file'], track['output_file'])
        audio.apply_metadata(artist=track['artist'], title=track['title'], apply_input=True)
        try:
            audio.move()
            mailer.append_table_data('moved to', track['output_file'])
        except:
            mailer.p('move unsuccessful')

    mailer.concat_table()
    mailer.send_mail()

@click.group()
def cli():
    pass

@cli.command()
def list_configs():
    try:
        contents = CONFIG_DIR.iterdir()
        for item in contents:
            click.echo(item.name)
    except Exception as e:
        click.echo(f'Error {e}')

@cli.group()
@click.option('--ftp', 'config_type', flag_value='ftp', help='FTP config')
@click.option('--rclone', 'config_type', flag_value='cloud', help='rclone/cloud config')
@click.option('--http', 'config_type', flag_value='http', help='HTTP(s) config')
@click.argument('config_file', type=click.Path(exists=False))
@click.pass_context
def modify(ctx, config_file, config_type):
    """
    Create, modify, or validate config settings.
    """
    ctx.ensure_object(dict)
    if 'ftp' in config_type:
        config = ConfigJSON(config_file, FTP_CONFIG)
        ctx.obj['remote_src'] = RadFTP(**config.FTP)
    elif 'cloud' in config_type:
        config = ConfigJSON(config_file, CLOUD_CONFIG)
        ctx.obj['remote_src'] = RadCloud(**config.cloud)
    elif 'http' in config_type:
        print(config_type)

    ctx.obj['config'] = config
    ctx.obj['mailer'] = RadMail(**config.email)

@modify.command()
@click.option('-f', '--filemap', is_flag=True, default=False, help='Create or edit the filemap for the given config.')
@click.pass_context
def edit(ctx, filemap):
    config = ctx.obj.get('config')
    if filemap:
        config.filemap_wizard_select()
    else:
        config.edit_config()


@modify.group()
def validate():
    """
    Validate config settings.
    """
    pass

@validate.command()
@click.pass_context
def email(ctx):
    """
    Validate email settings.
    """
    mailer = ctx.obj.get('mailer')
    mailer.validate()

@validate.command()
@click.pass_context
def remote(ctx):
    """
    Validate/list remote source
    """
    remote_src = ctx.obj.get('remote_src')
    remote_src.validate()

@cli.group()
@click.option('-v', '--verbose', is_flag=True, help='enable verbose mode')
@click.argument('config_file', type=click.Path(exists=False))
@click.pass_context
def run(ctx, verbose, config_file):
    if verbose:
        logger = RadLogger(LOG_FILE, verbose=True).get_logger()
    ctx.ensure_object(dict)
    ctx.obj['config'] = config_file

@run.command()
@click.pass_context
def rclone(ctx):
    config = ConfigJSON(ctx.obj.get('config'), CLOUD_CONFIG)
    mailer = RadMail(**config.email)
    cloud = RadCloud(**config.cloud)
    perform_standard(config, mailer, cloud)

@run.command()
@click.pass_context
def http(ctx):
    ctx.ensure_onject(dict)
    config = ConfigJSON(ctx.obj.get('config'), HTTP_CONFIG)

@run.group()
@click.pass_context
def ftp(ctx):
    ctx.ensure_object(dict)
    config = ConfigJSON(ctx.obj.get('config'), FTP_CONFIG)
    ctx.obj['config'] = config
    ctx.obj['mailer'] = RadMail(**config.email)
    ctx.obj['remote'] = RadFTP(**config.FTP)

@ftp.command()
@click.option('-t', '--tries', type=int, default=1, help='define number of tries')
@click.option('-s', '--sleep_timer', type=int, default=1200, help='define number of seconds between tries')
@click.pass_context
def news(ctx, tries, sleep_timer):
    config = ctx.obj.get('config')
    mailer = ctx.obj.get('mailer')
    ftp = ctx.obj.get('remote')
    tracks = config.filemap
    while tracks and tries > 0:
        mailer.message = ""
        for track in reversed(tracks):
            download = Path(config.dirs['download_dir'], track['input_file'])
            tmp = Path(config.dirs['audio_tmp'], track['input_file'])
            export = Path(config.dirs['export_dir'], track['output_file'])
            ftp.do_action(ftp.download_file, remote_file=track['input_file'], local_file=download)
            local = AudioFile(download, export)
            old = AudioFile(tmp)

            if local.analyse() == old.analyse():
                mailer.p(f'{track["input_file"]} has not been updated.')
            else:
                mailer.p(f'{track["input_file"]} has been updated.')
                tracks.remove(track)

            local.copy(tmp)
            local.apply_metadata(track['artist'], track['title'])
            local.move()
            mailer.add_attachment(old.input_file, 'mp3')
        tries -= 1
        if tracks and tries > 0:
            logger.info(f'Update incomplete. Attempts left: {tries}. Files left: {tracks}')
            mailer.subject = 'Update Incomplete'
            mailer.p('All files have not been updated')
            mailer.p(f'Will try {tries} more time.' if tries == 1 else f'Will try {tries} times')
            mailer.send_mail()
            logger.info(f'Sleeping for {sleep_timer} seconds.')
            sleep(sleep_timer)
        elif tracks and tries == 0:
            logger.info(f'Update incomplete. Files left: {tracks}. Giving up.')
            mailer.subject = 'Update Incomplete - Giving up'
            mailer.p('All files have not been update')
            mailer.p('Giving up.')
            mailer.send_mail()
        else:
            logger.info('Update complete')
            mailer.subject = 'Update Complete'
            mailer.p('All files have been updated')
            mailer.p('Goodbye')
            mailer.send_mail()

    click.echo(tries)
    click.echo(sleep_timer)

@ftp.command()
@click.pass_context
def standard(ctx):
    config = ctx.obj.get('config')
    mailer = ctx.obj.get('mailer')
    ftp = ctx.obj.get('remote')
    perform_standard(config, mailer, ftp)

