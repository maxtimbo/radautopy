import logging

from ..utils.audio import AudioFile
from ..utils.config import ROOT_DIR
from ..utils.utilities import handle_status_code

from . import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

def perform_ttwn(config, mailer, email_bool, remote):
    timestamp = remote.probe_timestamp()
    if handle_status_code(remote.manifest.status_code, mailer):
        try:
            url = remote.get_manifest(timestamp)
            logger.info('got manifest')
        except:
            logger.critical('could not get manifest')
            mailer.p('Could not get manifest')
            mailer.send_mail(alt_subject = 'An error occurred')

    remote_audio = remote.get_remote(url)
    config.concat_directories_filemap()
    track = config.filemap[0]
    if handle_status_code(remote_audio.status_code, mailer):
        if remote.download_file(remote_audio, track['input_file']):
            local_track = AudioFile(track['input_file'], track['output_file'])
            local_track.apply_metadata(track['artist'], track['title'])
            local_track.move()
            logger.info('successfully moved audio')
        else:
            mailer.p('Something went wrong')
            mailer.send_mail()




