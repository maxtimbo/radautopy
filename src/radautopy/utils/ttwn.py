import logging
import pathlib
import requests
import os

from requests.auth import HTTPBasicAuth
from datetime import datetime

from . import LOGGER_NAME
from .utilities import make_dirs
from .config import ROOT_DIR


logger = logging.getLogger(LOGGER_NAME)


class TTWN:
    def __init__(self, url: str, affiliate: str, username: str, password: str, timestamp_dir: pathlib.Path) -> None:
        self.url = url
        self.affiliate = affiliate
        self.username = username
        self.password = password
        self.timestamp_dir = pathlib.Path(timestamp_dir)
        self.remote_date_format = "%a, %d %b %Y %H:%M:%S GMT"
        self.local_date_format = "%Y%m%d%H%M%S"

        self.manifest = self.get_remote(os.path.join(self.url, self.affiliate, 'filemanifest.txt'))


    def probe_timestamp(self, new_timestamp: str = None) -> str:
        existing_timestamp = [x for x in self.timestamp_dir.glob('*.timestamp')]

        if new_timestamp == None and not existing_timestamp:
            default_timestamp = "20220325064459"
            pathlib.Path(self.timestamp_dir, f'{default_timestamp}.timestamp').touch()
            return default_timestamp
        elif new_timestamp == None and existing_timestamp:
            return existing_timestamp[0].stem
        else:
            existing_timestamp.unlink()
            pathlib.Path(self.timestamp_dir, f'{new_timestamp}.timestamp').touch()
            return new_timestamp

    def header_timestamp(self, req):
        return datetime.strptime(
                req.headers['last-modified'],
                self.remote_date_format
            ).strftime(
                self.local_date_format
            )

    def get_remote(self, url):
        return requests.get(url, auth=HTTPBasicAuth(self.username, self.password), timeout=20)

    def get_manifest(self, timestamp: str) -> str:
        modified = self.header_timestamp(self.manifest)

        if modified > timestamp:
            lines = self.manifest.iter_lines(decode_unicode=True)
            for line in lines:
                if "url" in line:
                    url = line.split('=')[1].replace('"', '').strip()
                    return url
        else:
            raise


    def download_file(self, remote, local):
        try:
            with open(local, 'wb') as audio:
                audio.write(remote.content)
            if int(remote.headers['content_length']) == os.stat(local).st_size:
                self.probe_timestamp(self.header_timestamp(remote.headers['last-modified']))
                return True
            else:
                return False
        except Exception as e:
            logger.exception(e)
            return False


