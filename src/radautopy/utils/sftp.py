import click
import logging
import pathlib

import paramiko

from . import LOGGER_NAME
from .errors import RemoteError
from .redact import MASK

SFTP_ERRORS = (paramiko.SSHException, OSError, EOFError)

logger = logging.getLogger(LOGGER_NAME)


class RadSFTP:
    def __init__(self, server: str, username: str, password: str, directory: str | None = None) -> None:
        self.server = server
        self.username = username
        self.password = password
        self.directory = directory
        self.sftp = None

    def connect(self) -> None:
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        if self.directory:
            self.sftp.chdir(self.directory)

    def do_action(self, function, pasv: bool = True, *args, **kwargs):
        try:
            with paramiko.Transport((self.server, 22)) as self.transport:
                self.transport.connect(username=self.username, password=self.password)
                self.connect()
                return function(*args, **kwargs)
        except RemoteError:
            raise
        except paramiko.AuthenticationException as e:
            raise RemoteError(f'SFTP {self.server}: authentication failed for {self.username}') from e
        except SFTP_ERRORS as e:
            raise RemoteError(f'SFTP {self.server}: {e or type(e).__name__}') from e

    def validate(self) -> None:
        click.echo('~~ SFTP Settings ~~')
        click.echo(f'server: {self.server}')
        click.echo(f'username: {self.username}')
        click.echo(f'password: {MASK}')
        click.echo(f'directory: {self.directory}')
        try:
            files = self.do_action(self.list_remote)
            for f in files:
                click.echo(f)
            click.echo('~~ SFTP Connection success! ~~')
        except Exception as e:
            click.echo(f'~~ SFTP Connection Failed! ~~\n{e}')

    def list_remote(self, filename: str | None = None) -> list[str]:
        files = self.sftp.listdir(path='.')
        if filename is not None:
            files = [f for f in files if f == filename]
        return files

    def download_file(self, remote_file: str, local_file: pathlib.Path | str) -> None:
        try:
            self.sftp.get(remote_file, local_file)
        except SFTP_ERRORS as e:
            pathlib.Path(local_file).unlink(missing_ok=True)
            raise RemoteError(f'SFTP {self.server}: download {remote_file} failed: {e}') from e
        logger.info(f"Downloaded {remote_file} as {local_file}")

    def download_files(self, file_map: list[tuple[str, pathlib.Path | str]]) -> None:
        for f in file_map:
            remote, local = f
            self.do_action(self.download_file, remote_file=remote, local_file=local)

