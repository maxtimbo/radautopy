import logging
import posixpath
import pathlib
import requests

from urllib.parse import urljoin

from . import LOGGER_NAME
from .utilities import make_dirs
from .config import ROOT_DIR


logger = logging.getLogger(LOGGER_NAME)


class TTWN:
    def __init__(self, url: str, affiliate: str, username: str, password: str) -> None:
        self.url = url
        self.affiliate = affiliate
        self.username = username
        self.password = password

        self.affiliate_dir = make_dirs(pathlib.Path(ROOT_DIR, affiliate))

        self.timestamp = self.get_timestamp()
        self.remote_manifest = urljoin(self.url, posixpath.join(self.affiliate, 'filemanifest.txt'))


        self.remote_date_format = "%a, %d %b %Y %H:%M:%S GMT"
        self.local_date_format = "%Y%m%d%H%M%S"

    def get_timestamp(self, new_timestamp: str = None) -> str:
        existing_timestamp = self.affiliate_dir.glob('*.timestamp')

        if new_timestamp == None and not exiting_timestamp:
            default_timestamp = "20220325064459"
            pathlib.Path(self.affiliate_dir, f'{default_timestamp}.timestamp').touch()
            return default_timestamp
        elif new_timestamp == None and existing_timestamp:
            return existing_timestamp[0].stem
        else:
            existing_timestamp.unlink()
            pathlib.Path(self.affiliate_dir, f'{new_timestamp}.timestamp').touch()
            return new_timestamp

    def get_remote(self, url):
        return requests.get(url, auth=HTTPBasicAuth(self.username, self.password), timeout=20)

    def get_manifest(self, modified, local) -> bool:

    def download_file(self, manifest):
        lines = manifest.iter_lines(decode_unicode=True)


