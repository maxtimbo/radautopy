import logging

from ..utils.audio import AudioFile
from ..utils.config import ROOT_DIR
from ..utils.utilities import handle_status_code

from . import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

def perform_ttwn(config, mailer, email_bool, remote):
    try:
        file_urls = remote.get_file_urls()
    except Exception as e:
        logger.critical(f"Could not get file list: {e}")
        mailer.p('Could not get file list')
        mailer.send_email(alt_subject='TTWN: An error occurred')
        return

    if not file_urls:
        logger.info('No new files available')
        return

    config.concat_directories_filemap()
    track = config.filemap[0]
    if remote.download_file(file_urls[0], track['input_file']):
        local_track = AudioFile(track['input_file'], track['output_file'])
        local_track.apply_metadata(track['artist'], track['title'])
        local_track.move()
        logger.info('successfully moved audio')
    else:
        mailer.p('Download failed')
        mailer.send_mail(alt_subject='TTWN: An error occurred')




