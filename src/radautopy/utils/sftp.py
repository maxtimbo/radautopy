import click
import logging
import traceback
import pathlib

import paramiko

from . import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


class RadSFTP:
    def __init__(self, server: str, username: str, password: str, directory: str = None) -> None:
        self.server = server
        self.username = username
        self.password = password
        self.directory = directory
        self.sftp = None

    def connect(self) -> None:
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        if self.directory is not None:
            self.sftp.chdir(self.directory)

    def do_action(self, function, pasv: bool = True, *args, **kwargs):
        with paramiko.Transport((self.server, 22)) as self.transport:
            self.transport.connect(username=self.username, password=self.password)
            self.connect()
            return function(*args, **kwargs)

    def validate(self) -> None:
        click.echo('~~ SFTP Settings ~~')
        click.echo(f'server: {self.server}')
        click.echo(f'username: {self.username}')
        click.echo(f'password: {self.password}')
        click.echo(f'directory: {self.directory}')
        try:
            files = self.do_action(self.list_remote)
            for f in files:
                click.echo(f)
            click.echo('~~ SFTP Connection success! ~~')
        except:
            click.echo('~~ SFTP Connection Failed! ~~')

    def list_remote(self, filename: str = None) -> list:
        files = []
        try:
            files = self.sftp.listdir(path='.')
            if filename is not None:
                files = [f for f in files if f == filename]
        except Exception as e:
            logger.exception(e)

        return files

    def download_file(self, remote_file: str, local_file: pathlib.Path | str) -> None:
        self.sftp.get(remote_file, local_file)
        logger.info(f"Downloaded {remote_file} as {local_file}")

    def download_files(self, file_map: list[tuple]) -> None:
        for f in file_map:
            remote, local = f
            self.do_action(self.download_file, remote_file=remote, local_file=local)

