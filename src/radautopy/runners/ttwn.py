import logging

from ..utils.audio import AudioFile
from ..utils.config.config import ConfigJSON
from ..utils.mail import RadMail

from . import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

def perform_ttwn(
        config: ConfigJSON,
        mailer: RadMail,
        email_mode: str,
        remote
    ) -> bool:

    file_urls = remote.get_file_urls()
    if not file_urls:
        logger.info('No new files available')
        return True

    config.concat_directories_filemap()
    track = config.filemap[0]
    if not remote.download_file(file_urls[0], track['input_file']):
        mailer.p(f'TTWN download failed: {file_urls[0]}')
        return False

    local_track = AudioFile(track['input_file'], track['output_file'])
    local_track.apply_metadata(track['artist'], track['title'])
    local_track.move()
    logger.info('successfully moved audio')
    mailer.p(f'Delivered {track["output_file"]}')
    return True
