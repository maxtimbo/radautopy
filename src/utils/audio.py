import datetime
import logging
import ffmpeg
import hashlib
import pathlib
import re
import shutil
import subprocess
import sys
import traceback

import taglib

logger = logging.getLogger('__main__')


class AudioFile:
    def __init__(self, input_file: pathlib.Path | str, output_file: pathlib.Path | str = None) -> None:
        self.input_file = input_file
        self.output_file = output_file

    @property
    def input_file(self) -> pathlib.Path:
        return self._input_file

    @input_file.setter
    def input_file(self, input_file: pathlib.Path | str) -> None:
        input_file = self.force_path(input_file)
        if input_file.exists():
            self._input_file = input_file
        else:
            logger.exception(FileNotFoundError(f"FileNotFound: {str(input_file)}"))
            raise FileNotFoundError(input_file)

    @property
    def output_file(self) -> pathlib.Path | None:
        if hasattr(self, '_output_file'):
            return self._output_file
        else:
            return None

    @output_file.setter
    def output_file(self, output_file: pathlib.Path | str) -> None:
        if output_file is not None:
            output_file = self.force_path(output_file)
            if output_file.is_dir():
                output_file = pathlib.Path(output_file, self.input_file.name)
            elif output_file.suffix == '':
                raise FileNotFoundError("Directory not found or filename invalid")
            if output_file == self.input_file:
                raise AttributeError("input_file and output_file cannot be the same")
            self._output_file = output_file

    def force_path(self, f: pathlib.Path | str) -> pathlib.Path:
        if isinstance(f, str):
            return pathlib.Path(f)
        else:
            return f

    def _create_output(self, new_filename: pathlib.Path | str = None) -> pathlib.Path:
        if not hasattr(self, '_output_file') and not new_filename:
            raise NameError("Either an output_file or a new_filename must be specified")
        elif not hasattr(self, '_output_file') or new_filename:
            self.output_file = self.force_path(new_filename)
        return self.output_file


    def _check_output(self, apply_input: bool = False) -> pathlib.Path:
        if hasattr(self, '_output_file') and not apply_input:
            return self.output_file
        else:
            return self.input_file

    def _logged_popen(self, cmd_line, *args, **kwargs):
        logger.debug(f'Running command: {subprocess.list2cmdline(cmd_line)}')
        return subprocess.Popen(cmd_line, *args, **kwargs)

    def apply_metadata(self, artist: str, title: str, apply_today: bool = False, apply_input: bool = False) -> None:
        audio = self._check_output(apply_input)

        if apply_today:
            today = datetime.datetime.today()
            today = today.strftime("%Y%m%d")
        else:
            today = ''

        with taglib.File(audio, save_on_exit=True) as cut:
            cut.tags["ARTIST"] = f"{artist} {today}"
            cut.tags["TITLE"] = title

    def convert(self) -> None:
        if not hasattr(self, 'output_file'):
            self.output_file = self.input_file.with_suffix(".mp3")
        try:
            out, err = (ffmpeg
                        .input(str(self.input_file))
                        .output(str(self.output_file))
                        .overwrite_output()
                        .run(capture_stdout = True, capture_stderr = True)
            )
            logger.debug(out)
        except ffmpeg.Error as e:
            logger.exception(e)
            logger.error(err)
            logger.error(out)

    def analyse(self, blocksize: int = 65536, apply_input: bool = True) -> None:
        audio = self._check_output(apply_input)
        logger.debug(f'analysing audio {audio}')
        hasher = hashlib.sha256()
        try:
            with open(audio, 'rb') as f:
                for block in iter(lambda: f.read(blocksize), b""):
                    hasher.update(block)
            self.hash = hasher.hexdigest()
            logger.debug(f'{audio} hash: {self.hash}')
            return self.hash
        except Exception as exc:
            logger.exception(Exception(traceback.format_exc()))

    def move_copy(self, new_filename: pathlib.Path | str = None, local_suffix: str = "_lm", apply_input: bool = True) -> None:
        audio_in = self._check_output(apply_input)
        audio_copy = self.force_path(new_filename)
        audio_copy_lm = audio_copy.with_suffix(audio_copy.suffix + local_suffix)
        try:
            shutil.copy(audio_in, audio_copy)
            shutil.copy(audio_in, audio_copy_lm)
            shutil.move(audio_in, self.output_file)
        except Exception as e:
            logger.exception(Exception(traceback.format_exc()))

    def move(self, new_filename: pathlib.Path | str = None, apply_input: bool = True) -> None:
        audio_in = self._check_output(apply_input)
        audio_out = self._create_output(new_filename)
        try:
            shutil.move(audio_in, audio_out)
        except Exception as e:
            logger.exception(Exception(traceback.format_exc()))

    def split_silence(self, threshold: int = -60, duration: int = 10) -> list:
        silence_start_re = re.compile(r' silence_start: (?P<start>[0-9]+(\.?[0-9]*))$')
        silence_end_re = re.compile(r' silence_end: (?P<end>[0-9]+(\.?[0-9]*)) ')
        total_duration_re = re.compile(r'size[^ ]+ time=(?P<hours>[0-9]{2}):(?P<minutes>[0-9]{2}):(?P<seconds>[0-9\.]{5}) bitrate=')
        p = self._logged_popen(
                (ffmpeg
                    .input(self.input_file)
                    .filter("silencedetect", f"{threshold}dB", duration)
                    .output('-', format='null')
                    .compile()
                 ) + ['-nostats'],
                stderr=subprocess.PIPE
            )
        output = p.communicate()[1].decode('utf-8')

        if p.returncode != 0:
            logger.critical("An error occured when running ffmpeg")
            logger.critical(output)
            sys.exit(1)

        logger.debug("~~ START FFMPEG SILENCE DETECT OUTPUT ~~")
        logger.debug(output)
        logger.debug("~~ END FFMPEG OUTPUT ~~")

        lines = output.splitlines()

        chunk_starts = []
        chunk_ends = []

        for line in lines:
            silence_start_match = silence_start_re.search(line)
            silence_end_match = silence_end_re.search(line)
            total_duration_match = total_duration_re.search(line)

            if silence_start_match:
                chunk_ends.append(float(silence_start_match.group('start')))
                if len(chunk_starts) == 0:
                    chunk_starts.append(0)
            elif silence_end_match:
                chunk_starts.append(float(silence_end_match.group('end')))
            elif total_duration_match:
                hours = int(total_duration_match.group('hours'))
                minutes = int(total_duration_match.group('minutes'))
                seconds = float(total_duration_match.group('seconds'))
                end_time = hours * 3600 + minutes * 60 + seconds

        if len(chunk_starts) == 0:
            chunk_starts.append(0)

        if len(chunk_starts) > len(chunk_ends):
            chunk_ends.append(end_time or 10_000_000)

        self.chunk_times = list(zip(chunk_starts, chunk_ends))

        cuts = []
        for i, (start_time, end_time) in enumerate(self.chunk_times):
            time = end_time - start_time
            out_filename = pathlib.Path(self.output_file.parent, self.output_file.stem + str(i + 1) + self.output_file.suffix)
            self._logged_popen(
                    (ffmpeg
                        .input(str(self.input_file), ss=start_time, t=time)
                        .output(str(out_filename))
                        .overwrite_output()
                        .compile()
                     ),
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE
            ).communicate()
            cuts.append(AudioFile(out_filename))

        return cuts

