import logging
import pathlib
import click

from rclone_python import rclone

from . import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


class RadCloud:
    def __init__(self, server: str, directory: str) -> None:
        self.server = server
        self.directory = directory
        self.full_path = f'{self.server}:{self.directory}'

    def download(self, filename: str, destination: pathlib.Path) -> None:
        rclone.copyto(f'{self.full_path}/{filename}', str(destination))
        logger.info(f'Successful download {filename} to {destination}')

    def download_files(self, file_map: list[tuple]) -> None:
        for f in file_map:
            remote, local = f
            self.download(remote, local)

    def validate(self) -> None:
        click.echo(rclone.tree(self.full_path))
