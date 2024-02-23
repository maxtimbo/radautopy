import click
import datetime
import json
import pathlib
import subprocess

from copy import copy
from tabulate import tabulate
from crontab import CronTab

from . import CONFIG_DIR, EMAIL_CONFIG, DEFAULT_DIRS, DEFAULT_FILEMAP, CLOUD_CONFIG, JOB_METADATA, FTP_CONFIG, RSS_CONFIG, TTWN_CONFIG
from .config import ConfigJSON
from .replace_fillers import ReplaceFillers
from ..utilities import make_dirs, SafeDict

def calculate_values(iterator: int, segments: int) -> tuple:
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

def build_dict(add_dict: dict) -> dict:
    return JOB_METADATA | add_dict | DEFAULT_DIRS | DEFAULT_FILEMAP

def set_cronjob(job_config: dict, config_file: str | pathlib.Path) -> None:
    config_file = config_file.name if isinstance(config_file, pathlib.Path) else config_file
    cron = CronTab(user=True)

    existing = cron.find_command(config_file)
    if existing:
        cron.remove(existing)

    radautopy = subprocess.check_output('which radautopy', shell = True).strip().decode()
    job = cron.new(command = f"{radautopy} {config_file} {job_config['job_runner']} {job_config['extra_args']}")
    job.set_comment(job_config['job_name'])
    job.setall(job_config['cron_expression'])
    cron.write()


class ConfigModify:
    def __init__(self, config_type: str = None, config_file: str = None) -> None:
        self.email_config: pathlib.Path = pathlib.Path(CONFIG_DIR, "email.json")
        if self.email_config.exists():
            self.email_dict = ConfigJSON().email_dict

        if config_file is not None:
            self.config_file: pathlib.Path = pathlib.Path(CONFIG_DIR, config_file)

        if config_type is not None:
            if 'ftp' in config_type:
                self.config_dict = build_dict(FTP_CONFIG)
            elif 'cloud' in config_type:
                self.config_dict = build_dict(CLOUD_CONFIG)
            elif 'rss' in config_type:
                self.config_dict = build_dict(RSS_CONFIG)
            elif 'ttwn' in config_type:
                self.config_dict = build_dict(TTWN_CONFIG)

    def set_email(self, config: dict = EMAIL_CONFIG) -> None:
        conf = self.set_interactive(config)
        self.save_config(conf, self.email_config)

    def set_config(self, config: dict = None) -> None:
        if config is None:
            config = self.config_dict
        else:
            self.config_dict = config
        conf = self.set_interactive(config)
        if click.confirm('Set email overrides?'):
            email_overrides = copy(self.email_dict['email'])
            if 'email' in conf:
                for k in conf['email']:
                    email_overrides[k] = conf['email'][k]

            updated = self.define_email_overrides(email_overrides)

            conf['email'] = {}
            for k, v in self.email_dict['email'].items():
                if v not in updated.values():
                    conf['email'][k] = updated[k]
        self.save_config(conf, self.config_file)

    def set_interactive(self, skel: dict) -> dict:
        for key in skel:
            if 'filemap' in key:
                self.filemap_wizard_select()
            else:
                click.echo(f'{"":=^50}\n{"Setting values for":=^50}\n{key:=^50}')
                for subkey, subval in skel[key].items():
                    if 'cron_expression' in subkey:
                        click.echo('Visit https://crontab.guru for help setting your cron expression')

                    if 'extra_args' in subkey:
                        click.echo('Extra args for cronjob. See `radautopy --help` for more info. In most cases, this can be left blank')


                    if 'job_type' in subkey:
                        skel[key][subkey] = click.prompt(f'Define {subkey}:', type=click.Choice(['ftp', 'cloud', 'rss', 'ttwn']), default=subval)
                    elif 'job_runner' in subkey:
                        skel[key][subkey] = click.prompt(f'Define {subkey}:', type=click.Choice(['news', 'standard', 'split_single', 'ttwn']), default=subval)
                    else:
                        click.echo(f'{subkey} = {subval}')
                        skel[key][subkey] = click.prompt(f'Define {subkey}:', default=subval)

        return skel


    def define_email_overrides(self, overrides: dict):
        override_table = [[i, k, v] for i, (k, v) in enumerate(overrides.items())]
        click.echo(tabulate(override_table, headers=['id', 'key', 'current value'], tablefmt='simple_outline'))

        selection = click.prompt('Select ID to edit: ', type = int)
        i, k, v = override_table[selection]
        overrides[k] = click.prompt(f'Define {k}', default=v)
        override_table = [[i, k, v] for i, (k, v) in enumerate(overrides.items())]
        click.echo(tabulate(override_table, headers=['id', 'key', 'current value'], tablefmt='simple_outline'))
        if click.confirm("Define another email override?"):
            self.define_email_overrides(overrides)

        return overrides

    def filemap_wizard_select(self) -> None:
        selection_table = [
            ['i', 'individual track edit'],
            ['f', 'filemap wizard'],
            ['q', 'quick show wizard'],
            ['s', 'skip filemap config']
        ]
        click.echo(tabulate(selection_table, tablefmt='simple_outline'))
        selection = click.prompt("", type=click.Choice([x[0] for x in selection_table], case_sensitive=False), show_choices=False)
        if 'i' in selection:
            self.select_track()
        elif 'f' in selection:
            self.set_filemap()
        elif 'q' in selection:
            self.quick_filemap()
        elif 's' in selection:
            return

    def select_track(self) -> None:
        for i, track in enumerate(self.config_dict['filemap']):
            click.echo(tabulate([[k, v] for k, v in track.items()], headers=['track id', i], tablefmt='simple_outline'))

        trackid = click.prompt('Select track to edit" ', type=int)
        set_track(self.config_dict['filemap'][trackid])
        if click.confirm('Set another?'):
            self.select_track()

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
            hour, segment = calculate_values(count, segments)
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
        condition = click.prompt('', type=click.Choice([x[0] for x in condition_table], case_sensitive=False), show_choices=False)

        if 'c' in condition:
            track = set_track({k:'' for k, v in DEFAULT_FILEMAP['filemap'][0].items()})
        elif 'd' in condition:
            track = set_track(track)
        elif 'q' in condition:
            return

        self.config_dict['filemap'].append(track)
        self._next_continue(track)

    def check_dirs(self, config: dict) -> None:
        if 'dirs' in config:
            for k, v in config['dirs'].items():
                click.echo(f'Attempting to create {k}')
                make_dirs(pathlib.Path(v))
                click.echo(f'{v} created')


    def save_config(self, config: dict, config_file: pathlib.Path) -> None:
        try:
            self.check_dirs(config)
            make_dirs(config_file.parents[0])
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)

            click.echo('Job saved successfully')
            if 'job' in config and click.confirm('Would you like to set the cronjob for this entry?'):
                click.echo(config['job']['cron_expression'])
                click.echo(config_file)
                set_cronjob(config['job'], config_file)
        except Exception as e:
            click.echo(e)


