import click
import feedparser
import logging
import lxml
import requests
import wget

from bs4 import BeautifulSoup
from . import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


class RadRSS:
    def __init__(self, url: str) -> None:
        self.url = url

    def get_rss_entry(self):
        logger.info(f'Traversing the RSS feed: {self.url}')
        feed = feedparser.parse(self.url)
        if feed.status != 200 and feed.status != 302:
            logger.critical(f'Issue with feed: {self.url} returned {feed.status}')
            raise

        newest_entry = feed.entries[0]
        newest_entry = newest_entry.link
        logger.info(f'{newest_entry = }')

        self.entry = newest_entry

    def get_download_link(self):
        try:
            entry_page = requests.get(self.entry)
        except Exception as e:
            logger.exception(e)
            raise

        soup = BeautifulSoup(entry_page.text, 'lxml')
        download_link = soup.find("a", {"title": "Download"})
        download_link = download_link['href']
        logger.info(f'{download_link = }')

        try:
            download_page = requests.get(download_link)
        except Exception as e:
            logger.exception(e)
            raise

        soup = BeautifulSoup(download_page.text, 'lxml')
        mp3_link = soup.find('div', class_='pod-content').find('a')
        mp3_link = mp3_link['href']
        logger.info(f'{mp3_link = }')

        self.download_link = mp3_link


    def download(self, download_dir):
        self.get_rss_entry()
        self.get_download_link()
        try:
            logger.info(f'Attempting download to {download_dir = }')
            local_file = wget.download(self.download_link, out=str(download_dir))
            logger.info(f'Download successful: {local_file = }')
            return local_file
        except Exception as e:
            logger.exception(e)
            raise

    def download_files(self):
        pass

    def validate(self):
        click.echo(f'Attempting {self.url = }')
        page = requests.get(self.url)
        if page.status_code != 200 and page.status_code != 302:
            click.echo(f'Issue with {self.url = } returned {page.status_code = }')
            raise
        try:
            self.get_rss_entry()
            click.echo(f'{self.entry = }')
            try:
                self.get_download_link()
                click.echo(f'{self.download_link = }')
            except Exception as e:
                click.echo(e)
                raise
        except Exception as e:
            click.echo(e)
            raise


#@dataclass
#class TTWN:
#    url: str
#    affiliate: str
#    username: str
#    password: str
