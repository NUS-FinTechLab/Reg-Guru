import os
from bs4 import BeautifulSoup

BASE_URL = "https://sso.agc.gov.sg"
CURRENT_BROWSE_URL = "Browse/Act/Current/All?PageSize=20&SortBy=Title&SortOrder=ASC"

class SsoScraper:
    def __init__(self, download_dir):
        self.base_url = BASE_URL

    def scrape(self, start_page=1, end_page=5):
        return
