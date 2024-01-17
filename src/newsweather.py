#!/usr/bin/python3
import logging
from pathlib import Path
from time import sleep

from utils.audio import AudioFile
from utils.cmdlts import BaseArgs
from utils.config import RadConfig
from utils.ftp import RadFTP
from utils.mail import RadMail, Attachment
from utils.settings import RadLogger, get_logger
import radftp.defaults as radftp
import defaults

DEFAULT_CONF = radftp.DEFAULT_CONFIG | defaults.DEFAULT_CONFIG
DEFAULT_CONF_FILE = Path(defaults.DEFAULT_CONFIG_DIR, "wsav", "wsav.ini")
LOG_FILE = Path(defaults.DEFAULT_LOG_DIR, "wsav", "wsav.log")
radftp.args_dict['prog'] = 'DBC News and Weather Downloader'
file_map = [('NEWSHIT.mp3', 'NEW1111.wav'), ('WXHIT.mp3', 'NEW1001.wav')]
file_map = [
    {
        'input_file'    :   'NEWSHIT.mp3',
        'output_file'   :   'NEW1111.wav',
        'artist'        :   'WJCL News',
        'title'         :   'WJCL News '
    },
    {
        'input_file'    :   'WXHIT.mp3',
        'output_file'   :   'NEW1001.wav',
        'artist'        :   'WJCL Weather',
        'title'         :   'WJCL Weather '
    }
]

logger = RadLogger(LOG_FILE, __name__).get_logger()


def Main():
    runners = [
        ('-t', '--tries',
            {'help': 'how many tries before giving up',
             'type': int,
             'required': True,
            }
        ),
        ('-s', '--sleep',
            {'help': 'override default sleep time. default time is 1200 seconds (20 minutes).',
             'type': int,
            }
        ),
    ]
    args = BaseArgs(radftp.args_dict, runners)
    if args.verbose:
        logger = RadLogger(LOG_FILE, __name__, verbose = True).get_logger(__name__)
        logger.setLevel(logging.DEBUG)

    if args.config is not None:
        config = RadConfig(DEFAULT_CONF, Path(args.config))
    else:
        config = RadConfig(DEFAULT_CONF, DEFAULT_CONF_FILE)

    mailer = RadMail('WJCL Mailer',
                     'subject',
                     config.email_reply,
                     config.email_recipient,
                     config.email_server,
                     config.email_port,
                     config.email_user,
                     config.email_passwd)

    mailer.add_footer('This is an automated messasge. Please reply to tfinley@dbcradio.com for questions.')

    if args.subparser == 'run':
        #sleep_time = if args.sleep is not None: args.sleep else: 1200
        files = config.ftp_files.split()
        while files and args.tries > 0:
            mailer.message = ""
            ftp = RadFTP(config.ftp_server, config.ftp_username, config.ftp_password, config.ftp_dir)
            for a in reversed(files):
                local = Path(config.download_dir, a)
                ftp.connect(ftp.download_file, remote_file=a, local_file=str(local))
                local = AudioFile(local, Path(config.export_dir, a))
                old = AudioFile(Path(config.audio_tmp, a))
                mailer.add_attachment(old.input_file, 'mp3')
                if local.analyse() == old.analyse():
                    mailer.p(f'{a} has not been updated.')
                else:
                    mailer.p(f'{a} has been updated.')
                    files.remove(a)

                local.move_copy(Path(config.audio_tmp, a))
            args.tries -= 1
            if files and args.tries > 0:
                logger.info(f'Update incomplete. Attempts left: {args.tries}. Files left: {files}')
                mailer.subject = 'Update Incomplete'
                mailer.p('All files have not been updated')
                mailer.p(f'Will try {args.tries} times')
                if args.email: mailer.send_mail()
                sleep(args.sleep if args.sleep is not None else 1200)
            elif files and args.tries == 0:
                logger.info(f'Update incomplete. Files left: {files}. Giving up.')
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
