import click
import datetime
import pathlib

from copy import copy
from tabulate import tabulate

from . import CONFIG_DIR, EMAIL_CONFIG, DEFAULT_DIRS, DEFAULT_FILEMAP, CLOUD_CONFIG, JOB_METADATA
from .replace_fillers import ReplaceFillers
from ..utilities import SafeDict

def calculate_values(iterator: int, segemtns: int) -> tuple:
    hour = (iterator - 1) // segments + 1
    segment = (iterator - 1) % segments + 1
    return hour, segment

def set_track(track: dict) -> dict:
    click.echo(tabulate([[k, v] for k, v in track.items()], tablefmt='simple_outline'))
    for k, v in track.items():
        track[k] = click.prompt(k, default=track[k])

    click.echo(tabulate([[k, v] for k, v in track.items()], tablefmt='simple_outline'))
    if not click.confirm('Confirm track data', default='y'):
        set_track(track)

    return track

class ConfigModify:
    def __init__(self, config_type: str, config_file: str) -> None:
        self.email_config: pathlib.Path = pathlib.Path(CONFIG_DIR, "email.json")
        self.config_file: pathlib.Path = pathlib.Path(CONFIG_DIR, config_file)

        defaults = JOB_METADATA | DEFAULT_DIRS | DEFAULT_FILEMAP
        if 'ftp' in config_type:
            self.config_dict = FTP_CONFIG | defaults
        elif 'cloud' in config_type:
            self.config_dict = CLOUD_CONFIG | defaults
        elif 'http' in config_type:
            raise NotImplementedError

    def set_email(self) -> None:
        self.set_interactive(EMAIL_CONFIG, self.email_config)

    def set_config(self) -> None:
        self.set_interactive(self.config_dict, self.config_file)
        if click.confirm('Set email overrides?'):
            email_overrides = copy(self.email_dict['email'])
            if 'email' in self.config_dict['email']:
                for k in self.config_dict['email']:
                    email_overrides[k] = self.config_dict['email'][k]

        updated = self.define_email_overrides(email_overrides)

        self.config_dict['email'] = {}
        for k, v in self.email_config['email'].items():
            if v not in updated.values():
                self.config_dict['email'][k] = updated[k]

    def set_interactive(self, skel: dict, config_file: pathlib.Path):
        for key in skel:
            if not 'filemap' in key:
                click.echo(f'{"":=^50}\n{"Setting values for":=^50}\n{key:=^50}')
                for subkey, subval in skel[key].items():
                    click.echo(f'{subkey} = {subval}')
                    skel[key][subkey] = click.prompt(f'Define {subkey}:', default=subval)
            else:
                self.filemap_wizard_select()

    def define_email_overrides(self, overrides: dict):
        override_table = [[i, k, v] for i, (k, v) in enumerate(override_table.items())]
        click.echo(tabulate(override_table, headers=['id', 'key', 'current value'], tablefmt='simple_outline'))

        selecton = click.prompt('Select ID to edit: ', type = int)
        i, k, v = override_table[selection]
        overrides[k] = click.prompt(f'Define {k}', default=v)
        override_table = [[i, k, v] for i, (k, v) in enumerate(override_table.items())]
        click.echo(tabulate(override_table, headers=['id', 'key', 'current value'], tablefmt='simple_outline'))
        if click.confirm("Define another email override?"):
            self.define_email_override(overrides)

        return overrides

    def filemap_wizard_select(self) -> None:
        selection = click.prompt("(i)ndividual track edit/(f)ilemap wizard/(q)uick show wizard", type=click.Choice(['i', 'f', 'q'], case_sensitive=False))
        if 'i' in selection:
            self.select_track()
        elif 'f' in selection:
            self.set_filemap()
        elif 'q' in selection:
            self.quick_filemap()

    def select_track(self) -> None:
        for i, track in enumerate(self.config_dict['filemap']):
            click.echo(tabulate([[k, v] for k, v in track.items()], headers=['track id', i], tablefmt='simple_outline'))

        trackid = click.prompt('Select track to edit" ', type=int)
        set_track(self.config_dict['filemap'][trackid])

    def set_filemap(self) -> None:
        for track in self.config_dict['filemap']:
            track = set_track(track)
        self._next_continue(track)

    def quick_filemap(self) -> None:
        trackobj = {k: '' for k, v in DEFAULT_FILEMAP['filemap'][0].items()}
        hours = click.prompt('How many hours?', type=int)
        segments = click.prompt('How many segments per hour?', type=int)
        iterator = hours * segments

        input_pattern = click.prompt('Define an input pattern: ', type=str)
        output_pattern = click.prompt('Define an output pattern: ', type=str)
        artist_pattern = click.prompt('Define an artist pattern: ', type=str)
        title_pattern = click.prompt('Define a title pattern: ', type=str)

        allowed_variables = {'hour', 'segment', 'count'}
        filemap = []

        for count in range(1, iterator + 1):
            hour, segment = self.calculate_values(count, segments)
            track = copy(trackobj)
            context = SafeDict(hour = hour, segment = segment, count = count)
            track['input_file'] = input_pattern.format_map(context)
            track['output_file'] = output_pattern.format_map(context)
            track['artist'] = artist_pattern.format_map(context)
            track['title'] = title_pattern.format_map(context)
            filemap.append(track)

        self.config_dict['filemap'] = filemap

    def _next_continue(self, track: dict) -> None:
        condition_table = [
            ['c', 'create a new track'],
            ['d', 'duplicate the last track'],
            ['q', 'quit']
        ]
        click.echo(tabulate(condition_table, tablefmt='simple_outline'))
        condition = click.prompt('', type=click.Choice([x[0] for x in condition_table]), case_sensitive=False, show_choices=False)

        if 'c' in condition:
            track = set_track({k:'' for k, v in DEFAULT_FILEMAP['filemap'][0].items()})
        elif 'd' in condition:
            track = set_track(track)
        elif 'q' in condition:
            return

        self.config_dict['filemap'].append(track)
        self._next_continue(track)

    def save_config(self, config: dict, config_file: pathlib.Path) -> None:
        try:
            make_dirs(config_file.parents[0])
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)

            logger.info(f'{config_file} saved sucessfully.')

        except Exception as e:
            logger.exception(e)


