import pathlib
from . import CONFIG_DIR, EMAIL_CONFIG, DEFAULT_DIRS, DEFAULT_FILEMAP, CLOUD_CONFIG
from ..utilities import SafeDict

class ConfigModify:
    def __init__(self, config_type: str, config_file: str) -> None:
        self.email_config: pathlib.Path = pathlib.Path(CONFIG_DIR, "email.json")
        self.config_file: pathlib.Path = pathlib.Path(CONFIG_DIR, config_file)

        defaults = DEFAULT_DIRS | DEFAULT_FILEMAP
        if 'ftp' in config_type:
            self.config_dict = FTP_CONFIG | defaults
        elif 'cloud' in config_type:
            self.config_dict = CLOUD_CONFIG | defaults
        elif 'http' in config_type:
            raise NotImplementedError

    def set_email(self):
        self.set_interactive(EMAIL_CONFIG, self.email_config)

    def set_config(self):
        self.set_interactive(self.config_dict, self.config_file)

    def set_interactive(self, skel: dict, config_file: pathlib.Path):
        for key in skel:
            if not 'filemap' in key:
                click.echo(f'{"":=^50}\n{"Setting values for":=^50}\n{key:=^50}')
                for subkey, subval in skel[key].items():
                    click.echo(f'{subkey} = {subval}')
                    skel[key][subkey] = click.prompt(f'Define {subkey}:', default=subval)



