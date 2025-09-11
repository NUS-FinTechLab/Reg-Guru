from bs4 import BeautifulSoup
import sys
import os
from urllib.parse import urlparse

# Add the parent directories to the Python path to resolve imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, src_dir)

from common.helper import downloadPdf, getHtml, getPdfLinks

BASE_URL = "https://www.fincen.gov"
ADVISORY_URL = "https://www.fincen.gov/resources/advisoriesbulletinsfact-sheets/advisories"

# Global variable for destination directory
DESTINATION_DIR = os.path.join(current_dir, '..', '..', '..', '..', 'data_ingestion', 'raw', 'us', 'fincen')

class FincenScraper:
    def __init__(self):
        self.baseUrl = BASE_URL
        self.advisoryUrl = ADVISORY_URL

    def scrape(self):
        html = getHtml(self.advisoryUrl)
        soup = BeautifulSoup(html, 'html.parser')
        
        advisoryLinks = set()
        current_url = self.advisoryUrl

        i = 0
        
        # Process all pages starting with the base URL
        while True:
            print(f"Scraping URL: {current_url}")
            
            # Get all links to responding advisory resources page
            links = soup.find_all('a', href=True)
            
            # Filter links that point to advisory resources
            links = [a['href'] for a in links if '/resources/advisories/' in a['href']]
            links = [self.baseUrl + link if link.startswith('/') else link for link in links]
            advisoryLinks.update(links)
            
            # Look for the next page link
            next_link = soup.find("a", class_="usa-pagination__next-page")
            if not next_link:
                break
                
            # Get the next page
            current_url = self.advisoryUrl + next_link['href']
            html = getHtml(current_url)
            soup = BeautifulSoup(html, 'html.parser')
            if i == 0: break
            
        files_information = []
            
        # Go into each advisory link and scrape the content
        pdfLinks = set()
        for link in advisoryLinks:
            html = getHtml(link)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Get all PDF links on the page
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.lower().endswith('.pdf'):
                    pdfLinks.add(href)
                    
            # Get the metadata (year, title)
            timeTag = soup.find("time")
            
            subjectField = soup.find("div", class_="field--name-field-advisory-subject")
            items = subjectField.find_all("div", class_="field__item")
            title = items[0].get_text(strip=True)
            
            print(timeTag, title)
            files_information.append({
                'url': link,
                'year': timeTag.get_text(strip=True) if timeTag else 'N/A',
                'title': title if title else 'N/A'
            })

        pdfLinks = [self.baseUrl + link if link.startswith('/') else link for link in pdfLinks]
            
        # Create destination directory if it doesn't exist
        os.makedirs(DESTINATION_DIR, exist_ok=True)
        
        downloaded_files = []
        for pdfLink in pdfLinks:
            print(f"Found PDF link: {pdfLink}")
            # Extract filename from URL
            parsed_url = urlparse(pdfLink)
            filename = os.path.basename(parsed_url.path)
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            # Create full destination path
            dest_path = os.path.join(DESTINATION_DIR, filename)
            downloadPdf(pdfLink, dest_path)
            downloaded_files.append(dest_path)
        
        return downloaded_files, files_information
