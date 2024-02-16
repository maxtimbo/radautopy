import click
import configparser
import datetime
import json
import logging
import pathlib

from copy import deepcopy, copy
from functools import partial
from tabulate import tabulate

from . import CONFIG_DIR, LOGGER_NAME, EMAIL_CONFIG, DEFAULT_DIRS, DEFAULT_FILEMAP
from ..utilities import make_dirs, SafeDict

logger = logging.getLogger(LOGGER_NAME)


class ConfigJSON:
    today   = datetime.datetime.today()

    def __init__(self, config_file: str, add_config: dict) -> None:
        self.email_config: pathlib.Path = pathlib.Path(CONFIG_DIR, "email.json")
        self.config_file: pathlib.Path = pathlib.Path(CONFIG_DIR, config_file)

        default_dict: dict = add_config | DEFAULT_DIRS | DEFAULT_FILEMAP

        self.email_dict = self._parse_json(self.email_config) if self.email_config.exists() else self.set_interactive(EMAIL_CONFIG, self.email_config)
        self.config_dict = self._parse_json(self.config_file) if self.config_file.exists() else self.set_interactive(default_dict, self.config_file)

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
            logger.debug('~'*10)
            for k, v in track.items():
                logger.debug(f'{k}: {v}')



    def edit_config(self) -> None:
        self.set_interactive(self.config_dict, self.config_file, True)
        if click.confirm('Would you like to edit the email config?'):
            self.set_interactive(self.email_dict, self.email_config)

    def set_interactive(self, config: dict, config_file: pathlib.Path, define_overides: bool = False) -> dict:
        print(f"You are now setting the values of {config_file}")
        print("Leave the value blank if you do not want to modify it.")
        print("Use absolute paths wherever a directory is required")
        for key in config:
            if 'filemap' in key:
                note = f'Skipping {key} for now.'
                print('\n' + note)
            else:
                note = f"Setting values for {key}"
                print('\n' + note)
                print('-'*len(note))
                for subkey, subval in config[key].items():
                    print(f'{subkey} = {subval}')
                    config[key][subkey] = click.prompt(f'Define {subkey}: ', default=subval)

        if define_overides and click.confirm('Set email overides?'):
            config['email'] = {}
            email_dict = [[i, k, v] for i, (k, v) in enumerate(self.email_dict['email'].items())]
            print(tabulate(email_dict, headers=['id', 'key', 'default value'], tablefmt='simple_outline'))
            selection = click.prompt('Select id to edit', type=int)
            print(email_dict[selection])
            print(email_dict[selection][0])
            k = email_dict[selection][1]
            print(email_dict[selection][2])
            config['email'][email_dict[selection][1]] = click.prompt(f'Define {email_dict[selection][1]}', default=email_dict[selection][2])

        print('\nPlease confirm config:')
        for key, value in config.items():
            if 'filemap' not in key:
                print(tabulate([[k, v] for k, v in config[key].items()], headers=[key, ''], tablefmt="simple_outline"))

        if click.confirm('\nAre these settings correct?'):
            if click.confirm(f'Write config file to {config_file}?'):
                self.save_config(config, config_file)
                self._set_attributes(config)
                return config
            else:
                return
        else:
            return config
            self.set_interactive(config, config_file)

    def save_config(self, config: dict, config_file: pathlib.Path) -> None:
        try:
            make_dirs(config_file.parents[0])
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)

            logger.info(f'{config_file} saved sucessfully.')

        except Exception as e:
            logger.exception(e)

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
                        track[k] = self._iter_ph(v)
                logger.debug(f"setting attr filemap: {self.filemap}")

    @staticmethod
    def calculate_values(iterator: int, segments: int) -> tuple:
        hour = (iterator - 1) // segments + 1
        segment = (iterator - 1) % segments + 1
        return hour, segment

    @staticmethod
    def set_track(track: dict) -> dict:
        print(tabulate([[key, value] for key, value in track.items()], tablefmt="simple_outline"))
        for k, v in track.items():
            track[k] = click.prompt(k, default=track[k])

        print(tabulate([[key, value] for key, value in track.items()], tablefmt="simple_outline"))
        if not click.confirm('Is this correct?', default='y'):
            ConfigJSON.set_track(track)

        return track

    def _iter_ph(self, orig: str) -> str:
        for ph, fn in self._replacement_functions.items():
            if ph in orig:
                orig = fn(orig, ph)
        return orig

    @staticmethod
    def _replace_placeholder(original: str, placeholder: str, value: str) -> str:
        return original.replace(placeholder, copy(value))

    _replacement_functions = {
        '{now}'     : partial(_replace_placeholder, value=today.strftime("%y%m%d %H:%M")),
        '{weekday}' : partial(_replace_placeholder, value=today.strftime("%A")),
        '{year}'    : partial(_replace_placeholder, value=today.strftime("%y")),
        '{month}'   : partial(_replace_placeholder, value=today.strftime("%m")),
        '{day}'     : partial(_replace_placeholder, value=today.strftime("%d")),
        '{week}'    : partial(_replace_placeholder, value=today.strftime("%V"))
    }

