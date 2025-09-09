import requests
from bs4 import BeautifulSoup
import sys
import os

# Add the parent directories to the Python path to resolve imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, src_dir)

from common.helper import getHtml

BASE_URL = "https://www.fincen.gov/resources/advisoriesbulletinsfact-sheets/advisories"

class FincenScraper:
    def __init__(self):
        self.baseUrl = BASE_URL
        pass

    def scrape(self):
        html = getHtml(self.baseUrl)
        soup = BeautifulSoup(html, 'html.parser')
        print(soup.prettify())