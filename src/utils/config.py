import click
import configparser
import datetime
import json
import logging
import pathlib

from copy import deepcopy, copy
from functools import partial
from tabulate import tabulate

from utils.cmdlts import make_dirs, SafeDict

logger = logging.getLogger()


class ConfigJSON:
    today   = datetime.datetime.today()

    def __init__(self, config_file: str, add_config: dict) -> None:
        self.global_config = pathlib.Path(DEFAULT_CONFIG_DIR, "global.json")
        self.config_file = pathlib.Path(DEFAULT_CONFIG_DIR, config_file)


        self.global_dict = self._parse_json(self.global_config) if self.global_config.exists() else self.set_interactive(GLOBAL_DICT)
        self.config_dict = self._parse_json(self.config_file) if self.config_file.exists() else self.set_interactive(default_dict)
        if self.config_dict is not None:
            self._set_attributes()

    def _parse_json(self, config_file: pathlib.Path) -> dict:
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.debug(f'{config_file} loaded sucessfully')
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

    def filemap_wizard_select(self) -> None:
        print(f"You are now setting up the filemap for {self.config_file}")
        print("Available variables are:")
        replacements = [[ph, func(placeholder=ph, original=ph)] for ph, func in self._replacement_functions.items()]
        print(tabulate(replacements, headers=['Variable', 'Example Output'], tablefmt="simple_outline"))
        print("\nUse these variables to create search patterns or replacement patterns.")
        print(f"For example: `input {{week}}{{year}}.mp3` would become `input {self.week}{self.year}.mp3`\n")
        print("You can choose to select an individual track to edit, use the filemap wizard, or use the quick show filemap wizard.")

        selection = click.prompt("(I)ndividual track edit/(F)ilemap wizard/(Q)uick show wizard", type=click.Choice(['i', 'f', 'q'], case_sensitive=False))
        if 'i' in selection:
            self.select_track()
        elif 'f' in selection:
            self.set_filemap()
        elif 'q' in selection:
            self.quick_filemap()

        self.save_config()

    def set_filemap(self) -> None:
        for track in self.config_dict['filemap']:
            track = self.set_track(track)
        self._next_continue(track)

    def quick_filemap(self) -> None:
        trackobj = {
             "input_file": "",
             "output_file": "",
             "artist": "",
             "title": ""
        }
        print("This is the quick filemap setup program.")
        print("Variables will be created for shows that follow a certain pattern.")
        hours = click.prompt("How many hours?", type=int)
        start_hour = click.confirm("Start hours from 1?", default='y')
        segments = click.prompt("How many segments per hour?", type=int)
        start_seg = click.confirm("Start segments from 1?", default='y')

        print('Use variables {hour} and {segment} where you need them. You can also use the other variables above')
        input_pattern = click.prompt("Define an input pattern: ", type=str)
        output_pattern = click.prompt("Define an output pattern: ", type=str)
        artist_pattern = click.prompt("Define an artist field pattern: ", type=str)
        title_pattern = click.prompt("Define a title field pattern: ", type=str)

        allowed_variables = {'hour', 'segment'}
        filemap = []

        for hour in range(hours):
            for segment in range(segments):
                track = copy(trackobj)
                context = SafeDict(hour= hour + 1 if start_hour else hour, segment= segment + 1 if start_seg else segment)
                track['input_file'] = input_pattern.format_map(context)
                track['output_file'] = output_pattern.format_map(context)
                track['artist'] = artist_pattern.format_map(context)
                track['title'] = title_pattern.format_map(context)
                filemap.append(track)

        self.config_dict['filemap'] = filemap


    def select_track(self) -> None:
        for i, track in enumerate(self.config_dict['filemap']):
            print(tabulate([[key, value] for key, value in track.items()], headers=['track id', i],  tablefmt="simple_outline"))

        trackid = click.prompt('Select a track to edit: ', type=int)
        self.set_track(self.config_dict['filemap'][trackid])

    def _next_continue(self, track: dict) -> None:
        cond = click.prompt('(C)reate a new track, (D)uplicate the last track, or (Q)uit?',
                            type=click.Choice(['c', 'd', 'q'], case_sensitive=False),
                            default='q')
        if 'c' in cond:
            track = self.set_track({k:"" for k, v in self.config_dict['filemap'][0].items()})
        elif 'd' in cond:
            track = self.set_track(track)
        elif 'q' in cond:
            return

        print(track)
        self.config_dict['filemap'].append(track)
        self._next_continue(track)

    def set_interactive(self, config_dict: dict = None):
        if config_dict != None:
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

        if click.confirm('\nAre these settings correct?'):
            if click.confirm(f'Write config file to {self.config_file}?'):
                self.save_config()
                self._set_attributes()
            else:
                return
        else:
            self.set_interactive()

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
        '{now}'     : partial(_replace_placeholder, value=today.strftime("%y%m%d %H:%M")),
        '{weekday}' : partial(_replace_placeholder, value=today.strftime("%A")),
        '{year}'    : partial(_replace_placeholder, value=today.strftime("%y")),
        '{month}'   : partial(_replace_placeholder, value=today.strftime("%m")),
        '{day}'     : partial(_replace_placeholder, value=today.strftime("%d")),
        '{week}'    : partial(_replace_placeholder, value=today.strftime("%U"))
    }

