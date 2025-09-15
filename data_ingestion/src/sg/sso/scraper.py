import os
from bs4 import BeautifulSoup

from data_ingestion.src.common.base_scraper import BaseScraper

BASE_URL = "https://sso.agc.gov.sg"
CURRENT_BROWSE_URL = "Browse/Act/Current/All?PageSize=20&SortBy=Title&SortOrder=ASC"

class SsoScraper(BaseScraper):
    def __init__(self, download_dir):
        super().__init__()
        self.base_url = BASE_URL

    def scrape(self, max_workers=10):
        return
