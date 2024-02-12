import feedparser
import logging
import lxml
import requests
import wget

from bs4 import BeautifulSoup
from . import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


class RadHTTP:
    def __init__(self, url: str) -> None:
        self.url = url

    def get_newest_entry(self):
        logger.info(f'Traversing the RSS feed: {self.url}')


    def download(self):
        pass

    def download_files(self):
        pass

    def validate(self):
        pass

@dataclass
class TTWN:
    url: str
    affiliate: str
    username: str
    password: str
