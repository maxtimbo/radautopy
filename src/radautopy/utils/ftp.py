import click
import logging
import traceback
import pathlib

from ftplib import FTP, error_perm

from . import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


class RadFTP:
    def __init__(self, server: str, username: str, password: str, pasv: bool, directory: str = None) -> None:
        self.server = server
        self.username = username
        self.password = password
        self.pasv = bool
        self.directory = directory

    def do_action(self, function, pasv: bool = True, *args, **kwargs):
        self.pasv = pasv
        with FTP(self.server) as self.ftp:
            self.ftp.login(user = self.username, passwd = self.password)
            self.ftp.set_pasv(self.pasv)
            if self.directory is not None:
                self.ftp.cwd(self.directory)
            return function(*args, **kwargs)

    def validate(self) -> None:
        click.echo('~~ FTP Settings ~~')
        click.echo(f'server: {self.server}')
        click.echo(f'username: {self.username}')
        click.echo(f'password: {self.password}')
        click.echo(f'directory: {self.directory}')
        try:
            files = self.do_action(self.list_remote)
            for f in files:
                click.echo(f)
            click.echo('~~ FTP Connection success! ~~')
        except:
            click.echo('~~ FTP Connection Failed! ~~')

    def list_remote(self, filename: str = None) -> list:
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

    def download_file(self, remote_file: str, local_file: pathlib.Path | str):
        try:
            self.ftp.nlst(remote_file)
            with open(local_file, 'wb') as f:
                self.ftp.retrbinary('RETR ' + remote_file, f.write, 1024)

            logger.info(f"Downloaded {remote_file} as {local_file}")
        except Exception as e:
            if str(e) == '550 The system cannot find the file specified. ':
                logger.exception(e)

            elif str(e) == '421 Control connection timed out ':
                logger.exception(e)
            else:
                logger.exception(e)

    def download_files(self, file_map: list[tuple]):
        for f in file_map:
            remote, local = f
            self.do_action(self.download_file, remote_file=remote, local_file=local)

