import logging

from . import LOGGER_NAME
from ..utils.audio import AudioFile
from ..utils.config.config import ConfigJSON
from ..utils.mail import RadMail

logger = logging.getLogger(LOGGER_NAME)

def perform_standard(
        config: ConfigJSON,
        mailer: RadMail,
        email_mode: str,
        remote
    ) -> bool:

    config.concat_directories_filemap()
    failed = 0
    for track in config.filemap:
        name = track['input_file'].name
        mailer.append_table_data('file', name)
        try:
            remote.download_files([(name, track['input_file'])])
            audio = AudioFile(track['input_file'], track['output_file'])
            audio.apply_metadata(artist=track['artist'], title=track['title'])
            audio.move()
        except Exception as e:
            failed += 1
            logger.exception(f'{name} failed: {e}')
            mailer.append_table_data('result', f'failed: {e}')
        else:
            logger.info(f'{name} delivered to {track["output_file"]}')
            mailer.append_table_data('result', f'delivered to {track["output_file"]}')

    total = len(config.filemap)
    if failed:
        mailer.p(f'{failed} of {total} file(s) failed')
    else:
        mailer.p(f'All {total} file(s) delivered')
    return failed == 0
