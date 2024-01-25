import configparser
import logging
import logging.config
import os
import pathlib
import traceback

from logging.handlers import RotatingFileHandler

from utils import DEFAULT_LOGGER_NAME
from utils.cmdlts import make_dirs

def get_logger(logger: str = DEFAULT_LOGGER_NAME) -> None:
    return logging.getLogger(logger)


class RadLogger:
    log_file: str = ''
    logger_name: str = DEFAULT_LOGGER_NAME
    LOGGING_CONFIG = dict(
        version=1,
        disable_existing_loggers=False,
        formatters={
            'precise': {
                'format': '%(asctime)s %(levelname)s:~ %(filename)s - %(module)s - %(funcName)s ~: %(message)s',
                'datefmt': '%Y%m%d %H:%M:%S'
            },
            'brief': {
                'format': '%(asctime)s %(levelname)s: %(message)s',
                'datefmt': '%Y%m%d %H:%M:%S'
            }
        },
        handlers={
            'stream': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
                'formatter': 'brief'
            },
            'file_handler': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'precise',
                'filename': log_file,
                'maxBytes': 1048576,
                'backupCount': 5
            },
        },
        loggers={
            logger_name: {
                'handlers': ['file_handler'],
                'level': 'INFO',
                'propagate': False
            }
        }
    )


    def __init__(self, log_file: pathlib.Path, logger_name: str = DEFAULT_LOGGER_NAME, verbose: bool = False) -> None:
        self.log_file = log_file
        make_dirs(self.log_file.parents[0])
        self.logger_name = logger_name

        self.LOGGING_CONFIG['handlers']['file_handler']['filename'] = self.log_file
        self.LOGGING_CONFIG['loggers'][self.logger_name] = {
                'handlers': ['file_handler'],
                'level': 'INFO',
                'propagate': False
            }

        if verbose:
            self.LOGGING_CONFIG['loggers'][self.logger_name]['handlers'].append('stream')
            self.LOGGING_CONFIG['loggers'][DEFAULT_LOGGER_NAME]['handlers'].append('stream')

        self.logging_conf = logging.config.dictConfig(self.LOGGING_CONFIG)
        self.logger = logging.getLogger(self.logger_name)

    @staticmethod
    def get_logger(logger_name: str = DEFAULT_LOGGER_NAME) -> logging.Logger:
        return logging.getLogger(logger_name)

    def set_level(self, level):
        self.logger.setLevel(level)


