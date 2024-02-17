import click
import json
import logging
import pathlib

from copy import deepcopy, copy
from tabulate import tabulate

from . import CONFIG_DIR, LOGGER_NAME, EMAIL_CONFIG, DEFAULT_DIRS, DEFAULT_FILEMAP
from .replace_fillers import ReplaceFillers
from ..utilities import make_dirs, SafeDict

logger = logging.getLogger(LOGGER_NAME)


class ConfigJSON:
    def __init__(self, config_file: str = None) -> None:
        self.email_config: pathlib.Path = pathlib.Path(CONFIG_DIR, "email.json")
        if self.email_config.exists():
            self.email_dict = self._parse_json(self.email_config)
        else:
            raise FileNotFoundError

        if config_file is not None:
            self.config_file: pathlib.Path = pathlib.Path(CONFIG_DIR, config_file)
            if self.config_file.exists():
                self.config_dict = self._parse_json(self.config_file)
            else:
                raise FileNotFoundError

    def _parse_json(self, config_file: pathlib.Path) -> dict:
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.debug(f'{config_file} loaded sucessfully')
            self._set_attributes(config)
            return config
        except Exception as e:
            logger.exception(e)

    def concat_directories_filemap(self):
        for i, track in enumerate(self.filemap):
            self.filemap[i]['input_file'] = pathlib.Path(self.dirs['download_dir'], track['input_file'])
            self.filemap[i]['output_file'] = pathlib.Path(self.dirs['export_dir'], track['output_file'])

        for track in self.filemap:
            logger.debug(f'{""=:^30}')
            for k, v in track.items():
                logger.debug(f'{k}: {v}')

    def _set_attributes(self, config: dict) -> None:
        for key in config:
            if 'filemap' not in key:
                if 'email' in key and hasattr(self, 'email'):
                    for k, v in config['email'].items():
                        self.email[k] = v
                        self.email_dict['email'][k] = v
                        logger.debug(f'overridding {k} to {v}')
                else:
                    setattr(self, key, deepcopy(config[key]))
                    logger.debug(f'setting attr {key} as {config[key]}')
            else:
                self.filemap = deepcopy(config['filemap'])
                for track in self.filemap:
                    for k, v in track.items():
                        track[k] = ReplaceFillers(v).track
                logger.debug(f"setting attr filemap: {self.filemap}")

