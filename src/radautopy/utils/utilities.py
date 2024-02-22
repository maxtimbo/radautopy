import logging
import pathlib

from . import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

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

def handle_status_code(status_code: int, mailer) -> bool:
    if status_code == 200:
        return handle_200()
    elif status_code == 404:
        return handle_error("File Not Found", mailer)
    elif status_code == 401:
        return handle_error("Authentication Error", mailer)
    elif status_code == 500:
        return handle_error("Server Error", mailer)
    else:
        return handle_error(f"Something went wrong: {status_code = }", mailer)

def handle_200() -> bool:
    return True

def handle_error(msg: str, mailer) -> bool:
    mailer.p(msg)
    mailer.send_mail(alt_subject = 'An Error Occured')
    return False

class SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'
