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

    def download(self, filename: str, destination: pathlib.Path) -> bool:
        try:
            rclone.copyto(f'{self.full_path}/{filename}', str(destination))
            logger.info(f'Successful download {filename} to {destination}')
            return True
        except Exception as e:
            logger.exception(e)
            return False

    def download_files(self, file_map: list[tuple]):
        for f in file_map:
            remote, local = f
            self.download(remote, local)

    def validate(self):
        click.echo(rclone.tree(self.full_path))
