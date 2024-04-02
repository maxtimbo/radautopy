import logging

from . import LOGGER_NAME
from ..utils.audio import AudioFile

logger = logging.getLogger(LOGGER_NAME)

def perform_standard(config, mailer, email_bool, remote):
    config.concat_directories_filemap()
    downloads = [(x['input_file'].name, x['input_file']) for x in config.filemap]
    logger.info(f'{downloads = }')
    try:
        logger.debug('try started')
        remote.download_files(downloads)
        for i, o in downloads:
            logger.info(f'downloaded: {i}')
            mailer.append_table_data('downloaded', i)
        logger.debug('try complete')
    except:
        logger.error('downloads unsuccessful')
        mailer.p('Download unsuccessful')
    else:
        logger.debug('else clause started')
        for track in config.filemap:
            audio = AudioFile(track['input_file'], track['output_file'])
            logger.debug(f'audio object created {track["input_file"]} -> {track["output_file"]}')
            audio.apply_metadata(artist=track['artist'], title=track['title'])
            logger.debug(f'applied metadata {track["artist"]} {track["title"]}')
            try:
                audio.move()
                logger.debug('audio moved')
                mailer.append_table_data('moved to', track['output_file'])
            except:
                logger.error('move fail')
                mailer.p('move unsuccessful')
    finally:
        logger.debug('finally clause')
        mailer.concat_table()
        if email_bool: mailer.send_mail()

