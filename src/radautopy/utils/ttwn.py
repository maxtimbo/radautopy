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
    def __init__(self, url: str, affiliate: str, api_key: str) -> None:
        self.url = url
        self.affiliate = affiliate
        self.api_key = api_key
        self.headers = {
                "X-API-Key": api_key,
                "User-Agent": "tten_download_script_radautopy"
        }

    def get_file_urls(self) -> list[str]:
        """Fetch the list of new file URLs from the API.

        Returns a list of download URLs (one per file), or an empty list if there are no new files.
        """
        url = f"{self.url}/audio/{self.affiliate}/newFiles"
        response = requests.get(url, headers = self.headers, timeout = 30)
        response.raise_for_status()

        return [line.strip() for line in response.text.splitlines() if line.strip()]

    def download_file(self, file_url: str, local_path: pathlib.Path | str) -> bool:
        """Download an audio file from the API.

        The API returns a 302 redirect to a signed CloudFront URL.
        requests.get() follows this redirect automatically.

        Returns True on success, False on failure.
        """
        try:
            response = requests.get(file_url, headers = self.headers, timeout = 60, allow_redirects = True)
            response.raise_for_status()

            with open(local_path, 'wb') as audio:
                audio.write(response.content)

            expected_size = int(response.headers.get('content-length', 0))
            actual_size = os.stat(local_path).st_size
            if expected_size and expected_size != actual_size:
                logger.error(f"Size mismatch: expected {expected_size}, got {actual_size}")
                return False

            return True
        except Exception as e:
            logger.exception(e)
            return False

    def validate(self) -> None:
        """Test the API connection."""
        url = f"{self.url}/audio/{self.affiliate}/newFiles"
        response = requests.get(url, headers=self.headers, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            lines = [l for l in response.text.splitlines() if l.strip()]
            print(f"Files available: {len(lines)}")
        else:
            print(f"Error: {response.text}")


