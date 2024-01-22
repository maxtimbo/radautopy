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
        config = ConfigJSON(Path(defaults.DEFAULT_CONFIG_DIR, args.config), DEFAULT_CONF)
    else:
        config = ConfigJSON(DEFAULT_CONF_FILE, DEFAULT_CONF)

    base.args.config = config

    config.email['sender'] = 'Standard FTP Mailer'
    config.email['subject'] = 'Standard Subject'
    mailer = RadMail(**config.email)
    mailer.add_footer('This is an automated messasge. Please reply to tfinley@dbcradio.com for questions.')
    ftp = RadFTP(**config.FTP)

    base.validators.append(mailer.validate)
    base.validators.append(ftp.validate)

    base.builtins()

    if args.subparser == 'run':
        tracks = config.filemap

if __name__ == '__main__':
    Main()
