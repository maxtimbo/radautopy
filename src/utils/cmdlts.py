import argparse
import logging
import pathlib
import traceback

from typing import Callable

logger = logging.getLogger('__main__')


def make_dirs(path: pathlib.Path | str):
    if pathlib.Path.is_dir(path):
        logger.info(f'{path} already exists')
    else:
        try:
            pathlib.Path.mkdir(path, parents=True)
            logger.info(f'{path} created')
        except FileNotFoundError as exc:
            logger.exception(FileNotFoundError(traceback.format_exc()))
            raise
    return path


class BaseArgs:
    def __init__(self, varis: dict, runner_args: list[tuple] = None) -> None:
        helptext = varis['description'] + "\nCreate a new config file by using the edit_config option. Config files are stored in ~/.config/radautopy by default."

        self.parser = argparse.ArgumentParser(prog=varis['prog'], description=helptext)
        group = self.parser.add_mutually_exclusive_group()
        subparsers = self.parser.add_subparsers(dest='subparser')

        group.add_argument('--edit_config', help='edit or create a new config', action='store_true')
        group.add_argument('--edit_filemap', help='edit or create a new filemap', action="store_true")

        self.parser.add_argument('--config', help='config file')
        self.parser.add_argument('-v', '--verbose', help='verbose output to stdout', action='store_true')

        run = subparsers.add_parser('run')
        run.add_argument('-e', '--email', help='email output', action='store_true')
        #run.add_argument('-d', '--dry_run', help='dry run; emails will not be sent, files will not be downloaded.', action='store_true')
        if runner_args is not None:
            for arg in runner_args:
                run.add_argument(*arg[:-1], **arg[-1])

        #validate = subparsers.add_parser('validate')
        #validate.add_argument('-e', '--email', help='validate and test email settings', action='store_true')

    def get_args(self) -> argparse.ArgumentParser:
        self.args = self.parser.parse_args()
        return self.args

    def builtins(self):
        if self.args.edit_config:
            self.args.config.set_interactive()

        if self.args.edit_filemap:
            self.args.config.filemap_wizard_select()



#def BaseArgs(varis: dict, runner_args: list[tuple] = None) -> argparse.ArgumentParser:
#    helptext = varis['description'] + "\nCreate a new config file by using the edit_config option. Config files are stored in ~/.config/radautopy by default."
#    parser = argparse.ArgumentParser(prog=varis['prog'], description=helptext)
#    group = parser.add_mutually_exclusive_group()
#    subparsers = parser.add_subparsers(dest='subparser')
#
#    group.add_argument('--edit_config', help='edit or create a new config')
#    group.add_argument('--edit_filemap', help='edit or create a new filemap')
#
#    parser.add_argument('--config', help='config file')
#    parser.add_argument('-v', '--verbose', help='verbose output to stdout', action='store_true')
#
#    run = subparsers.add_parser('run')
#    run.add_argument('-e', '--email', help='email output', action='store_true')
#    run.add_argument('-d', '--dry_run', help='dry run; emails will not be sent, files will not be downloaded.', action='store_true')
#    if runner_args is not None:
#        for arg in runner_args:
#            run.add_argument(*arg[:-1], **arg[-1])
#
#    validate = subparsers.add_parser('validate')
#    validate.add_argument('-e', '--email', help='validate and test email settings', action='store_true')
#
#    args = parser.parse_args()
#
#    return args


class SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'
