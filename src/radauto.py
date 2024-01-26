#!/usr/bin/python3

import argparse
from pathlib import Path
from time import sleep

from utils import LOG_DIR, FTP_CONFIG
from utils.audio import AudioFile
from utils.config import ConfigJSON
from utils.ftp import RadFTP
from utils.mail import RadMail, Attachment
from utils.log_setup import RadLogger

LOG_FILE = Path(LOG_DIR, "radautopy.log")

logger = RadLogger(LOG_FILE).get_logger()

def Main():
    parser = argparse.ArgumentParser(prog="Radio Automation Python", description="")
    parser.add_argument('--config')
    parser.add_argument('-v', '--verbose')

    edit_group = parser.add_mutually_exclusive_group()
    edit_group.add_argument('--edit_config', action='store_true')
    edit_group.add_argument('--edit_filemap', action='store_true')

    job_type = parser.add_subparsers(dest='job_type')
    job_group = job_type.add_mutually_exclusive_group()
    job_group.add_argument('--cloud', action='store_true')
    job_group.add_argument('--ttwn', action='store_true')
    ftp_job = job_type.add_subparsers(dest='ftp_job')
    ftp_job.add_mut
    job_group.add_argument('--ftp', action='store_true')

    validators = parser.add_subparsers(dest='validators')

