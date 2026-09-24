import click
import feedparser
import logging
import requests
import wget

from bs4 import BeautifulSoup
from . import LOGGER_NAME
from .errors import RemoteError

logger = logging.getLogger(LOGGER_NAME)


class RadRSS:
    def __init__(self, url: str) -> None:
        self.url = url

    def _get(self, url: str) -> requests.Response:
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
        except requests.RequestException as e:
            raise RemoteError(f'RSS: request to {url} failed: {e}') from e
        return response

    def get_rss_entry(self) -> None:
        logger.info(f'Traversing the RSS feed: {self.url}')
        feed = feedparser.parse(self.url)
        status = feed.get('status')
        if status is None:
            raise RemoteError(f'RSS: could not read feed {self.url}: {feed.get("bozo_exception", "no response")}')
        if status not in (200, 301, 302):
            raise RemoteError(f'RSS: feed {self.url} returned HTTP {status}')
        if not feed.entries:
            raise RemoteError(f'RSS: feed {self.url} has no entries')

        newest_entry = feed.entries[0].link
        logger.info(f'{newest_entry = }')

        self.entry = newest_entry

    def get_download_link(self) -> None:
        soup = BeautifulSoup(self._get(self.entry).text, 'lxml')
        download_link = soup.find("a", {"title": "Download"})
        if download_link is None or not download_link.get('href'):
            raise RemoteError(f'RSS: no Download link found on {self.entry}')
        download_link = download_link['href']
        logger.info(f'{download_link = }')

        soup = BeautifulSoup(self._get(download_link).text, 'lxml')
        content = soup.find('div', class_='pod-content')
        mp3_link = content.find('a') if content else None
        if mp3_link is None or not mp3_link.get('href'):
            raise RemoteError(f'RSS: no mp3 link found on {download_link}')
        mp3_link = mp3_link['href']
        logger.info(f'{mp3_link = }')

        self.download_link = mp3_link

    def download(self, download_dir: str) -> str:
        self.get_rss_entry()
        self.get_download_link()
        logger.info(f'Attempting download to {download_dir = }')
        try:
            local_file = wget.download(self.download_link, out=str(download_dir))
        except Exception as e:
            raise RemoteError(f'RSS: download {self.download_link} failed: {e}') from e
        logger.info(f'Download successful: {local_file = }')
        return local_file

    def validate(self) -> None:
        click.echo(f'Attempting {self.url = }')
        try:
            self.get_rss_entry()
            click.echo(f'{self.entry = }')
            self.get_download_link()
            click.echo(f'{self.download_link = }')
            click.echo('~~ RSS feed ok ~~')
        except Exception as e:
            click.echo(f'~~ RSS feed check failed! ~~\n{e}')


#@dataclass
#class TTWN:
#    url: str
#    affiliate: str
#    username: str
#    password: str
