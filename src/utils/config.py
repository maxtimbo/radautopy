import click
import configparser
import datetime
import json
import logging
import pathlib

from functools import partial
from utils.cmdlts import make_dirs


logger = logging.getLogger('__main__')


class FileMap:
    today   = datetime.datetime.today()
    now     = today.strftime("%y%m%d %H:%M")
    weekday = today.strftime("%A")
    year    = today.strftime("%y")
    week    = today.strftime("%U")

    def __init__(self, config_file: pathlib.Path) -> None:
        self.config_file = config_file
        self.file_map = self._parse_json()

    def _parse_json(self) -> list[dict]:
        try:
            with open(self.config_file, 'r') as fmap:
                file_map = json.load(fmap)
            logger.debug(f'{self.config_file} successfully loaded.')

            for track in file_map:
                for key, value in track.items():
                    for placeholder, func in self._replacement_functions.items():
                        if placeholder in value:
                            track[key] = func(placeholder=placeholder, original=value)
            return file_map
        except Exception as e:
            logger.exception(e)

    @staticmethod
    def _replace_placeholder(original: str, placeholder: str, value: str) -> str:
        return original.replace(placeholder, value)

    _replacement_functions = {
        '{now}'     : partial(_replace_placeholder, value=now),
        '{weekday}' : partial(_replace_placeholder, value=weekday),
        '{year}'    : partial(_replace_placeholder, value=year),
        '{week}'    : partial(_replace_placeholder, value=week)
    }


class ConfigJSON:
    today   = datetime.datetime.today()
    now     = today.strftime("%y%m%d %H:%M")
    weekday = today.strftime("%A")
    year    = today.strftime("%y")
    week    = today.strftime("%U")

    def __init__(self, config_file: pathlib.Path, default_dict: dict) -> None:
        self.config_file = config_file
        self.config_dict = self._parse_json() if self.config_file.exists() else self.set_interactive(default_dict)
        self._set_attributes()

    def _parse_json(self) -> dict:
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)

            logger.debug(f'{self.config_file} loaded sucessfully')

            if 'filemap' in config:
                for track in config['filemap']:
                    for key, value in track.items():
                        for placeholder, func in self._replacement_functions.items():
                            if placeholder in value:
                                logger.debug(f'Setting {track[key]}')
                                track[key] = func(placeholder=placeholder, original=value)
                                logger.debug(f'Results: {track[key]}')

            return config
        except Exception as e:
            logger.exception(e)

    def set_interactive(self, config_dict: dict):
        self.config_dict = config_dict
        print(f"You are now setting the values of {self.config_file}")
        print("Leave the value blank if you do not want to modify it.")
        print("Use absolute paths wherever a directory is required")
        for key in self.config_dict:
            if 'filemap' in key:
                note = f'Skipping {key} for now.'
                print('\n' + note)
                print('-'*len(note))
            else:
                note = f"Setting values for {key}"
                print('\n' + note)
                print('-'*len(note))
                for subkey, subval in self.config_dict[key].items():
                    print(f'{subkey} = {subval}')
                    try:
                        self.config_dict[key][subkey] = str(input(f'Define {subkey}: ') or subval)
                    except EOFError:
                        return

        print('\nPlease confirm config:')
        for key, value in self.config_dict.items():
            if 'filemap' not in key:
                print(f'[{key}]')
                for subkey, subval in self.config_dict[key].items():
                    print(f"{subkey} = {subval}")

        if not click.confirm('\nAre these settings correct?'):
            self.set_interactive()
        else:
            if click.confirm(f'Write config file to {self.config_file}?'):
                self.save_config()
                self._set_attributes()

    def save_config(self) -> None:
        try:
            make_dirs(self.config_file.parents[0])
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_dict, f, ensure_ascii=False, indent=4)

            logger.info(f'{self.config_file} saved sucessfully.')

        except Exception as e:
            logger.exception(e)

    def _set_attributes(self) -> None:
        for key in self.config_dict:
            if 'filemap' not in key:
                setattr(self, key, self.config_dict[key])
                logger.debug(f'setting attr {key} as {self.config_dict[key]}')
            else:
                setattr(self, 'filemap', self.config_dict['filemap'])
                logger.debug(f"setting attr filemap: {self.config_dict['filemap']}")

    @staticmethod
    def _replace_placeholder(original: str, placeholder: str, value: str) -> str:
        return original.replace(placeholder, value)

    _replacement_functions = {
        '{now}'     : partial(_replace_placeholder, value=now),
        '{weekday}' : partial(_replace_placeholder, value=weekday),
        '{year}'    : partial(_replace_placeholder, value=year),
        '{week}'    : partial(_replace_placeholder, value=week)
    }


class RadConfig:
    def __init__(self, config_dict: dict, config_file: pathlib.Path) -> None:
        self.config_dict = config_dict
        self.config_file = config_file
        if self.check_config():
            self.get_config()

    def check_config(self) -> bool:
        if not self.config_file.exists():
            if click.confirm(f'The config file {self.config_file} does not exist. Would you like to create one now?'):
                self.set_interactive()
                return True
            else:
                return False
        else:
            return True

    def get_config(self) -> configparser.ConfigParser:
        conf = configparser.ConfigParser()
        conf.read(self.config_file)
        self.config_dict = {s:dict(conf.items(s)) for s in conf.sections()}
        self.validate_dirs()
        self.set_attributes()

    def validate_dirs(self) -> None:
        for directory in self.config_dict['dirs']:
            make_dirs(pathlib.Path(self.config_dict['dirs'][directory]))

    def save_config(self) -> None:
        self.conf = configparser.ConfigParser()
        for key in self.config_dict:
            self.conf[key] = self.config_dict[key]

        make_dirs(self.config_file.parents[0])
        with open(self.config_file, 'w') as f:
            self.conf.write(f)

    def set_interactive(self) -> None:
        print(f"You are now setting the values of {self.config_file}")
        print("Leave the value blank if you do not want to modify it.")
        print("Use absolute paths wherever a directory is required")
        for key in self.config_dict:
            note = f"Setting values for {key}"
            print('\n' + note)
            print('-'*len(note))
            for subkey, subval in self.config_dict[key].items():
                print(f'{subkey} = {subval}')
                try:
                    self.config_dict[key][subkey] = str(input(f'Define {subkey}: ') or subval)
                except EOFError:
                    return

        print('\nPlease confirm config:')
        for key, value in self.config_dict.items():
            print(f'[{key}]')
            for subkey, subval in self.config_dict[key].items():
                print(f"{subkey} = {subval}")

        if not click.confirm('\nAre these settings correct?'):
            self.set_interactive()
        else:
            if click.confirm(f'Write config file to {self.config_file}?'):
                self.save_config()

    def set_attributes(self) -> None:
        for key in self.config_dict:
            setattr(self, key, self.config_dict[key])
            logger.debug(f'setting attr {key} as {self.config_dict[key]}')
            for subkey in self.config_dict[key]:
                logger.debug(f'setting attr {subkey} as {self.config_dict[key][subkey]}')
                if 'dirs' in key:
                    setattr(self, subkey, pathlib.Path(self.config_dict[key][subkey]))
                else:
                    setattr(self, subkey, self.config_dict[key][subkey])


