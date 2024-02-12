import argparse
import logging
import pathlib
import traceback

from typing import Callable

from . import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

class BaseArgs:
    def __init__(self, varis: dict, runner_args: list[tuple] = None) -> None:
        program, helptext = varis.values()
        helptext = helptext + "\nConfig files are stored in ~/radautopy/config by default."
        self.validators: list = []

        self.parser = argparse.ArgumentParser(prog=program, description=helptext)
        group = self.parser.add_mutually_exclusive_group()
        subparsers = self.parser.add_subparsers(dest='subparser')

        group.add_argument('--edit_config', help='edit a new config', action='store_true')
        group.add_argument('--edit_filemap', help='edit or create a new filemap', action="store_true")

        self.parser.add_argument('--config', help='config file')
        self.parser.add_argument('-v', '--verbose', help='verbose output to stdout', action='store_true')

        run = subparsers.add_parser('run')
        run.add_argument('-e', '--email', help='email output', action='store_true')
        #run.add_argument('-d', '--dry_run', help='dry run; emails will not be sent, files will not be downloaded.', action='store_true')
        if runner_args is not None:
            for arg in runner_args:
                run.add_argument(*arg[:-1], **arg[-1])

        validate = subparsers.add_parser('validate')
        validate.add_argument('-l', '--list_remote', help='list remote files.', action='store_true')

    def get_args(self) -> argparse.ArgumentParser:
        self.args = self.parser.parse_args()
        return self.args

    def builtins(self):
        if self.args.edit_config:
            self.args.config.edit_config()

        if self.args.edit_filemap:
            self.args.config.filemap_wizard_select()

        if self.args.subparser == 'validate':
            if self.args.list_remote:
                pass
            else:
                for func in self.validators:
                    results = func()


