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

@cli.command()
@click.pass_context
def standard(ctx):
    config = ctx.obj.get('config')
    mailer = ctx.obj.get('mailer')
    ftp = ctx.obj.get('remote')
    perform_standard(config, mailer, ftp)

