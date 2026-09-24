import click
import logging
import pathlib

from ftplib import FTP, all_errors, error_perm

from . import LOGGER_NAME
from .errors import RemoteError
from .redact import MASK

logger = logging.getLogger(LOGGER_NAME)


class RadFTP:
    def __init__(self, server: str, username: str, password: str, pasv: bool, directory: str | None = None) -> None:
        self.server = server
        self.username = username
        self.password = password
        self.pasv = pasv
        self.directory = directory

    def do_action(self, function, pasv: bool = True, *args, **kwargs):
        self.pasv = pasv
        try:
            with FTP(self.server, timeout=60) as self.ftp:
                self.ftp.login(user = self.username, passwd = self.password)
                self.ftp.set_pasv(self.pasv)
                if self.directory:
                    self.ftp.cwd(self.directory)
                return function(*args, **kwargs)
        except RemoteError:
            raise
        except all_errors as e:
            raise RemoteError(f'FTP {self.server}: {e}') from e

    def list_remote(self, filename: str | None = None) -> list[str]:
        files = [] if filename is not None else ""
        try:
            if filename is not None:
                files = self.ftp.nlst(filename)
            else:
                files = self.ftp.nlst()
        except error_perm as resp:
            if str(resp) == '550 No files found':
                logger.critical("No files in this directory")
            else:
                raise

        if filename is None:
            files = list(filter(None, files))

            for f in files:
                logger.debug(f)

        return files

    def download_file(self, remote_file: str, local_file: pathlib.Path | str) -> None:
        try:
            self.ftp.nlst(remote_file)
            with open(local_file, 'wb') as f:
                self.ftp.retrbinary('RETR ' + remote_file, f.write, 1024)
        except all_errors as e:
            pathlib.Path(local_file).unlink(missing_ok=True)
            raise RemoteError(f'FTP {self.server}: download {remote_file} failed: {e}') from e

        logger.info(f"Downloaded {remote_file} as {local_file}")

    def download_files(self, file_map: list[tuple[str, pathlib.Path | str]]) -> None:
        for f in file_map:
            remote, local = f
            self.do_action(self.download_file, remote_file=remote, local_file=local)

    def validate(self) -> None:
        click.echo('~~ FTP Settings ~~')
        click.echo(f'server: {self.server}')
        click.echo(f'username: {self.username}')
        click.echo(f'password: {MASK}')
        click.echo(f'directory: {self.directory}')
        try:
            files = self.do_action(self.list_remote)
            for f in files:
                click.echo(f)
            click.echo('~~ FTP Connection success! ~~')
        except Exception as e:
            click.echo(f'~~ FTP Connection Failed! ~~\n{e}')

