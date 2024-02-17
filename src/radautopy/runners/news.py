import logging

from pathlib import Path
from time import sleep

from . import LOGGER_NAME
from ..utils.audio import AudioFile

logger = logging.getLogger(LOGGER_NAME)

def perform_news(config, mailer, remote, tries, sleep_timer):
    tracks = config.filemap
    while tracks and tries > 0:
        mailer.message = ""
        for track in reversed(tracks):
            download = Path(config.dirs['download_dir'], track['input_file'])
            tmp = Path(config.dirs['audio_tmp'], track['input_file'])
            export = Path(config.dirs['export_dir'], track['output_file'])
            remote.do_action(remote.download_file, remote_file=track['input_file'], local_file=download)
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

