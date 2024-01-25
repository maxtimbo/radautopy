import pathlib

logger = logging.getLogger()

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

class SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'
