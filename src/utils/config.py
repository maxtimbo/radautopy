import click
import configparser
import datetime
import json
import logging
import pathlib

from copy import deepcopy, copy
from functools import partial
from tabulate import tabulate

from utils.cmdlts import make_dirs


logger = logging.getLogger('__main__')


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
            return config
        except Exception as e:
            logger.exception(e)

    def set_filemap(self) -> None:
        print(f"You are now setting up the filemap for {self.config_file}")
        print("Available variables are:")
        replacements = [[ph, func(placeholder=ph, original=ph)] for ph, func in self._replacement_functions.items()]
        print(tabulate(replacements, headers=['Variable', 'Example Output'], tablefmt="simple_outline"))
        print("\nUse these variables to create search patterns or replacement patterns.")
        print(f"For example: `input {{week}}{{year}}.mp3` would become `input {self.week}{self.year}.mp3`\n")

        for track in self.config_dict['filemap']:
            track = self.set_track(track)

        self._next_continue(track)
        self.save_config()

    def select_track(self) -> None:
        for i, track in enumerate(self.config_dict['filemap']):
            print(tabulate([[key, value] for key, value in track.items()], headers=['track id', i],  tablefmt="simple_outline"))

        trackid = click.prompt('Select a track to edit: ', type=int)
        self.set_track(self.config_dict['filemap'][trackid])
        self.save_config()

    def _next_continue(self, track: dict):
        cond = click.prompt('(C)reate a new track, (D)uplicate the last track, or (Q)uit?',
                            type=click.Choice(['c', 'd', 'q'], case_sensitive=False),
                            default='q')
        if 'c' in cond:
            track = self.set_track({k:"" for k, v in self.config_dict['filemap'][0].items()})
            print(track)
            self.config_dict['filemap'].append(track)
            self._next_continue(track)
        elif 'd' in cond:
            track = self.set_track(track)
            print(track)
            self.config_dict['filemap'].append(track)
            self._next_continue(track)

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
                setattr(self, key, deepcopy(self.config_dict[key]))
                logger.debug(f'setting attr {key} as {self.config_dict[key]}')
            else:
                self.filemap = deepcopy(self.config_dict['filemap'])
                for track in self.filemap:
                    for k, v in track.items():
                        track[k] = self._iter_ph(v)
                logger.debug(f"setting attr filemap: {self.filemap}")

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
        '{now}'     : partial(_replace_placeholder, value=now),
        '{weekday}' : partial(_replace_placeholder, value=weekday),
        '{year}'    : partial(_replace_placeholder, value=year),
        '{week}'    : partial(_replace_placeholder, value=week)
    }


#class RadConfig:
#    def __init__(self, config_dict: dict, config_file: pathlib.Path) -> None:
#        self.config_dict = config_dict
#        self.config_file = config_file
#        if self.check_config():
#            self.get_config()
#
#    def check_config(self) -> bool:
#        if not self.config_file.exists():
#            if click.confirm(f'The config file {self.config_file} does not exist. Would you like to create one now?'):
#                self.set_interactive()
#                return True
#            else:
#                return False
#        else:
#            return True
#
#    def get_config(self) -> configparser.ConfigParser:
#        conf = configparser.ConfigParser()
#        conf.read(self.config_file)
#        self.config_dict = {s:dict(conf.items(s)) for s in conf.sections()}
#        self.validate_dirs()
#        self.set_attributes()
#
#    def validate_dirs(self) -> None:
#        for directory in self.config_dict['dirs']:
#            make_dirs(pathlib.Path(self.config_dict['dirs'][directory]))
#
#    def save_config(self) -> None:
#        self.conf = configparser.ConfigParser()
#        for key in self.config_dict:
#            self.conf[key] = self.config_dict[key]
#
#        make_dirs(self.config_file.parents[0])
#        with open(self.config_file, 'w') as f:
#            self.conf.write(f)
#
#    def set_interactive(self) -> None:
#        print(f"You are now setting the values of {self.config_file}")
#        print("Leave the value blank if you do not want to modify it.")
#        print("Use absolute paths wherever a directory is required")
#        for key in self.config_dict:
#            note = f"Setting values for {key}"
#            print('\n' + note)
#            print('-'*len(note))
#            for subkey, subval in self.config_dict[key].items():
#                print(f'{subkey} = {subval}')
#                try:
#                    self.config_dict[key][subkey] = str(input(f'Define {subkey}: ') or subval)
#                except EOFError:
#                    return
#
#        print('\nPlease confirm config:')
#        for key, value in self.config_dict.items():
#            print(f'[{key}]')
#            for subkey, subval in self.config_dict[key].items():
#                print(f"{subkey} = {subval}")
#
#        if not click.confirm('\nAre these settings correct?'):
#            self.set_interactive()
#        else:
#            if click.confirm(f'Write config file to {self.config_file}?'):
#                self.save_config()
#
#    def set_attributes(self) -> None:
#        for key in self.config_dict:
#            setattr(self, key, self.config_dict[key])
#            logger.debug(f'setting attr {key} as {self.config_dict[key]}')
#            for subkey in self.config_dict[key]:
#                logger.debug(f'setting attr {subkey} as {self.config_dict[key][subkey]}')
#                if 'dirs' in key:
#                    setattr(self, subkey, pathlib.Path(self.config_dict[key][subkey]))
#                else:
#                    setattr(self, subkey, self.config_dict[key][subkey])
#
#
