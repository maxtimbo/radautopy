#!/usr/bin/python3
import logging
from pathlib import Path
from time import sleep

from utils.audio import AudioFile
from utils.cmdlts import BaseArgs
from utils.config import ConfigJSON
from utils.ftp import RadFTP
from utils.mail import RadMail, Attachment
from utils.settings import RadLogger, get_logger
import radftp.defaults as radftp
import defaults

DEFAULT_CONF = radftp.DEFAULT_CONFIG | defaults.DEFAULT_CONFIG | defaults.DEFAULT_FILEMAP
DEFAULT_CONF_FILE = Path(defaults.DEFAULT_CONFIG_DIR, "standardftp", "standardftp.json")
LOG_FILE = Path(defaults.DEFAULT_LOG_DIR, "standardftp", "standardftp.log")

logger = RadLogger(LOG_FILE, __name__).get_logger()


def Main():
    base = BaseArgs(radftp.args_dict)
    args = base.get_args()
    if args.verbose:
        logger = RadLogger(LOG_FILE, __name__, verbose = True).get_logger(__name__)
        logger.setLevel(logging.DEBUG)

    if args.config is not None:
        config = ConfigJSON(Path(args.config), DEFAULT_CONF)
    else:
        config = ConfigJSON(DEFAULT_CONF_FILE, DEFAULT_CONF)

    base.args.config = config
    base.builtins()

    config.email['sender'] = 'WJCL Mailer'
    config.email['subject'] = 'Standard Subject'

    mailer = RadMail(config.email)

    mailer.add_footer('This is an automated messasge. Please reply to tfinley@dbcradio.com for questions.')

    if args.subparser == 'run':
        tracks = config.filemap
        while tracks and args.tries > 0:
            mailer.message = ""
            ftp = RadFTP(config.FTP['server'], config.FTP['username'], config.FTP['password'], config.FTP['dir'])
            for track in reversed(tracks):
                ftp.do_action(ftp.download_file, remote_file=track['input_file'], local_file=Path(config.dirs['download_dir'], track['input_file']))
                local = AudioFile(Path(config.dirs['download_dir'], track['input_file']), Path(config.dirs['export_dir'], track['output_file']))
                old = AudioFile(Path(config.dirs['audio_tmp'], track['output_file']))
                if local.analyse() == old.analyse():
                    mailer.p(f'{track["input_file"]} has not been updated.')
                else:
                    mailer.p(f'{track["input_file"]} has been updated.')
                    tracks.remove(track)

                local.move_copy(Path(config.dirs['audio_tmp'], track['input_file']))
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
