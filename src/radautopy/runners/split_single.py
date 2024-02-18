import click
import shutil
from ..utils.audio import AudioFile

def perform_split_single(config, mailer, remote, threshold, duration):
    local_file = AudioFile(remote.download(config.dirs['download_dir']), config.dirs['audio_tmp'])
    mailer.p(f'Download Success {local_file.input_file.name = }')
    split_audio = local_file.split_silence(threshold, duration)
    config.concat_directories_filemap()
    for track, files in zip(split_audio, config.filemap):
        mailer.append_table_data('slice', track.input_file.name)
        mailer.append_table_data('output', files["output_file"])
        track.output_file = files['output_file']
        track.apply_metadata(files['artist'], files['title'])
        track.move()

    local_file.input_file.unlink()

    mailer.concat_table()
    mailer.send_mail()
