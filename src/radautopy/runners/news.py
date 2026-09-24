import logging

from pathlib import Path
from time import sleep

from . import LOGGER_NAME
from ..utils.audio import AudioFile
from ..utils.config.config import ConfigJSON
from ..utils.mail import RadMail

logger = logging.getLogger(LOGGER_NAME)

def perform_news(
        config: ConfigJSON,
        mailer: RadMail,
        email_mode: str,
        remote,
        tries: int,
        sleep_timer: int
    ) -> bool:

    tracks = list(config.filemap)
    while tracks and tries > 0:
        mailer.message = ""
        mailer.attachments = []
        for track in list(tracks):
            download = Path(config.dirs['download_dir'], track['input_file'])
            tmp = Path(config.dirs['audio_tmp'], track['input_file'])
            export = Path(config.dirs['export_dir'], track['output_file'])
            try:
                remote.do_action(remote.download_file, remote_file=track['input_file'], local_file=download)
                local = AudioFile(download, export)
                updated = not tmp.exists() or local.analyse() != AudioFile(tmp).analyse()

                if updated:
                    mailer.p(f'{track["input_file"]} has been updated.')
                    tracks.remove(track)
                else:
                    mailer.p(f'{track["input_file"]} has not been updated.')

                local.copy(tmp)
                local.apply_metadata(track['artist'], track['title'])
                local.move()
                mailer.add_attachment(tmp, 'mp3')
            except Exception as e:
                logger.exception(f'{track["input_file"]} failed: {e}')
                mailer.p(f'{track["input_file"]} failed: {e}')

        tries -= 1
        if tracks and tries > 0:
            logger.info(f'Update incomplete. Attempts left: {tries}. Files left: {tracks}')
            mailer.subject = 'Update Incomplete'
            mailer.p('All files have not been updated')
            mailer.p(f'Will try {tries} more time.' if tries == 1 else f'Will try {tries} more times.')
            if email_mode == 'always':
                mailer.send_mail()
            logger.info(f'Sleeping for {sleep_timer} seconds.')
            sleep(sleep_timer)

    if tracks:
        logger.info(f'Update incomplete. Files left: {tracks}. Giving up.')
        mailer.subject = 'Update Incomplete - Giving up'
        mailer.p('All files have not been updated')
        mailer.p('Giving up.')
        return False

    logger.info('Update complete')
    mailer.subject = 'Update Complete'
    mailer.p('All files have been updated')
    mailer.p('Goodbye')
    return True
