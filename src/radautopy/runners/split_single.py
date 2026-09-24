import logging

from . import LOGGER_NAME
from ..utils.audio import AudioFile
from ..utils.config.config import ConfigJSON
from ..utils.errors import AudioError
from ..utils.mail import RadMail

logger = logging.getLogger(LOGGER_NAME)

def perform_split_single(
        config: ConfigJSON,
        mailer: RadMail,
        email_mode: str,
        remote,
        threshold: int,
        duration: int
    ) -> bool:

    local_file = AudioFile(remote.download(config.dirs['download_dir']), config.dirs['audio_tmp'])
    mailer.p(f'Download Success {local_file.input_file.name}')
    split_audio = local_file.split_silence(threshold, duration)
    config.concat_directories_filemap()
    if len(split_audio) != len(config.filemap):
        mailer.p(f'Warning: found {len(split_audio)} segment(s) but the filemap has {len(config.filemap)} track(s)')
    if not split_audio:
        raise AudioError(f'no audio segments found in {local_file.input_file.name}')

    for track, files in zip(split_audio, config.filemap):
        mailer.append_table_data('slice', track.input_file.name)
        mailer.append_table_data('output', files["output_file"])
        track.output_file = files['output_file']
        track.apply_metadata(files['artist'], files['title'])
        track.move()

    local_file.input_file.unlink(missing_ok=True)
    return len(split_audio) == len(config.filemap)
