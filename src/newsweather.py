#!/usr/bin/python3
import logging
from pathlib import Path
from time import sleep

from utils import ARGS_DICT, LOG_DIR, FTP_CONFIG
from utils.audio import AudioFile
from utils.baseargs import BaseArgs
from utils.config import ConfigJSON
from utils.ftp import RadFTP
from utils.mail import RadMail, Attachment
from utils.log_setup import RadLogger

DEFAULT_CONF_FILE = "newsweather.json"
LOG_FILE = Path(LOG_DIR, "newsweather.log")
ARGS_DICT['program'] = 'DBC News and Weather Downloader'

logger = RadLogger(LOG_FILE).get_logger()


def Main():
    runners = [
        ('-t', '--tries', {
            'help': 'how many tries before giving up',
            'type': int,
            'required': True,
            }
        ),
        ('-s', '--sleep', {
            'help': 'override default sleep time. default time is 1200 seconds (20 minutes).',
            'type': int,
            }
        ),
    ]
    base = BaseArgs(ARGS_DICT, runners)
    args = base.get_args()
    if args.verbose:
        logger = RadLogger(LOG_FILE, verbose = True).get_logger()
        logger.setLevel(logging.DEBUG)

    if args.config is not None:
        config = ConfigJSON(args.config, FTP_CONFIG)
    else:
        config = ConfigJSON(DEFAULT_CONF_FILE, FTP_CONFIG)

    base.args.config = config

    mailer = RadMail(**config.email)
    ftp = RadFTP(**config.FTP)

    base.validators.append(mailer.validate)
    base.validators.append(ftp.validate)

    base.builtins()

    if args.subparser == 'run':
        tracks = config.filemap
        while tracks and args.tries > 0:
            mailer.message = ""
            for track in reversed(tracks):
                download = Path(config.dirs['download_dir'], track['input_file'])
                tmp = Path(config.dirs['audio_tmp'], track['input_file'])
                export = Path(config.dirs['export_dir'], track['output_file'])
                ftp.do_action(ftp.download_file, remote_file=track['input_file'], local_file=download)
                local = AudioFile(download, export)
                old = AudioFile(tmp)
                if local.analyse() == old.analyse():
                    mailer.p(f'{track["input_file"]} has not been updated.')
                else:
                    mailer.p(f'{track["input_file"]} has been updated.')
                    tracks.remove(track)

                local.copy(tmp)
                local.apply_metadata(track['artist'], track['title'])
                local.move()
                mailer.add_attachment(old.input_file, 'mp3')
            args.tries -= 1
            if tracks and args.tries > 0:
                sleep_timer = args.sleep if args.sleep is not None else 1200
                logger.info(f'Update incomplete. Attempts left: {args.tries}. Files left: {tracks}')
                mailer.subject = 'Update Incomplete'
                mailer.p('All files have not been updated')
                mailer.p(f'Will try {args.tries} more time.' if args.tries == 1 else f'Will try {args.tries} times')
                if args.email: mailer.send_mail()
                logger.info(f'Sleeping for {sleep_timer} seconds.')
                sleep(sleep_timer)
            elif tracks and args.tries == 0:
                logger.info(f'Update incomplete. Files left: {tracks}. Giving up.')
                mailer.subject = 'Update Incomplete - Giving up'
                mailer.p('All files have not been update')
                mailer.p('Giving up.')
                if args.email: mailer.send_mail()
            else:
                logger.info('Update complete')
                mailer.subject = 'Update Complete'
                mailer.p('All files have been updated')
                mailer.p('Goodbye')
                if args.email: mailer.send_mail()



if __name__ == '__main__':
    Main()
