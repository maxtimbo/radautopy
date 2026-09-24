import logging
import pathlib
import click

from rclone_python import rclone
from rclone_python.utils import RcloneException

from . import LOGGER_NAME
from .errors import RemoteError

logger = logging.getLogger(LOGGER_NAME)


class RadCloud:
    def __init__(self, server: str, directory: str | None = None) -> None:
        self.server = server
        self.directory = (directory or '').strip('/')
        self.full_path = f'{self.server}:{self.directory}'

    def _remote_path(self, filename: str) -> str:
        return f'{self.full_path}/{filename}' if self.directory else f'{self.full_path}{filename}'

    # rclone is connectionless; kept so runners can treat every remote the same
    def do_action(self, function, pasv: bool = True, *args, **kwargs):
        return function(*args, **kwargs)

    def list_remote(self, filename: str | None = None) -> list[str]:
        try:
            files = [f['Name'] for f in rclone.ls(self.full_path, max_depth=1, files_only=True)]
        except RcloneException as e:
            raise RemoteError(f'rclone {self.full_path}: listing failed: {self._reason(e)}') from e
        if filename is not None:
            files = [f for f in files if f == filename]
        return files

    def download_file(self, remote_file: str, local_file: pathlib.Path | str) -> None:
        try:
            rclone.copyto(self._remote_path(remote_file), str(local_file), show_progress=False, args=['--retries 1'])
        except RcloneException as e:
            raise RemoteError(f'rclone {self.full_path}: download {remote_file} failed: {self._reason(e)}') from e
        logger.info(f'Downloaded {remote_file} as {local_file}')

    @staticmethod
    def _reason(e: Exception) -> str:
        lines = [l for l in str(e).splitlines() if l.strip()]
        return lines[-1] if lines else type(e).__name__

    def download_files(self, file_map: list[tuple[str, pathlib.Path | str]]) -> None:
        for f in file_map:
            remote, local = f
            self.do_action(self.download_file, remote_file=remote, local_file=local)

    def validate(self) -> None:
        click.echo('~~ rclone Settings ~~')
        click.echo(f'server: {self.server}')
        click.echo(f'directory: {self.directory}')
        try:
            files = self.do_action(self.list_remote)
            for f in files:
                click.echo(f)
            click.echo('~~ rclone Connection success! ~~')
        except Exception as e:
            click.echo(f'~~ rclone Connection Failed! ~~\n{e}')
