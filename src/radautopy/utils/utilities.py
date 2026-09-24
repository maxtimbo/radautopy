import logging
import os
import pathlib
import sys

from . import LOGGER_NAME
from .errors import ConfigError

logger = logging.getLogger(LOGGER_NAME)

def radautopy_executable() -> str:
    candidate = pathlib.Path(sys.executable).parent / "radautopy"
    return str(candidate) if candidate.exists() else "radautopy"

def make_dirs(path: pathlib.Path | str) -> pathlib.Path:
    try:
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise ConfigError(f"{path}: permission denied for uid {os.getuid()}; check ownership, or that the share is mounted into the container") from e
    except OSError as e:
        raise ConfigError(f"{path}: cannot create directory ({e.strerror})") from e
    logger.info(f'{path} ready')
    return path


def check_writable(path: pathlib.Path | str) -> None:
    make_dirs(path)
    if not os.access(path, os.W_OK | os.X_OK):
        raise ConfigError(f"{path}: not writable by uid {os.getuid()}; check ownership or mount options")

class SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'
