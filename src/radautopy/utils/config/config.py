import logging
import pathlib

from copy import deepcopy

from . import CONFIG_DIR, LOGGER_NAME, EMAIL_CONFIG, DEFAULT_DIRS, DEFAULT_FILEMAP
from . import store
from .replace_fillers import ReplaceFillers
from ..errors import ConfigError
from ..redact import redact

logger = logging.getLogger(LOGGER_NAME)

REQUIRED_SECTIONS = ["job", "dirs", "filemap"]

class ConfigJSON:
    def __init__(self, config_file: str | None = None) -> None:
        self.email_config: pathlib.Path = pathlib.Path(CONFIG_DIR, "email.json")
        if not store.exists("email.json"):
            raise ConfigError("email config not found; set it up on the Email Config page first")
        self.email_dict = self._parse_json("email.json")
        if "email" not in self.email_dict:
            raise ConfigError("email config has no 'email' section")

        if config_file is not None:
            self.config_file: pathlib.Path = pathlib.Path(CONFIG_DIR, config_file)
            if not store.exists(config_file):
                raise ConfigError(f"job config {config_file} not found")
            self.config_dict = self._parse_json(config_file)
            missing = [k for k in REQUIRED_SECTIONS if k not in self.config_dict]
            if missing:
                raise ConfigError(f"{config_file} is missing section(s): {', '.join(missing)}")

    def _parse_json(self, filename: str) -> dict:
        try:
            config = store.get(filename)
        except Exception as e:
            raise ConfigError(f"could not load {filename}: {e}") from e
        if not isinstance(config, dict):
            raise ConfigError(f"{filename} is not a JSON object")
        logger.debug(f'{filename} loaded sucessfully')
        self._set_attributes(config)
        return config

    def concat_directories_filemap(self) -> None:
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
                        logger.debug(f'overridding {k} to {redact({k: v})[k]}')
                else:
                    setattr(self, key, deepcopy(config[key]))
                    logger.debug(f'setting attr {key} as {redact(config[key])}')
            else:
                self.filemap = deepcopy(config['filemap'])
                for track in self.filemap:
                    for k, v in track.items():
                        track[k] = ReplaceFillers(v).track
                logger.debug(f"setting attr filemap: {self.filemap}")

