from ast import parse
import os
import sys
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Add the parent directories to the Python path to resolve imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, src_dir)

from common.helper import downloadPdf, getHtml, getPdfLinks
from common.base_scraper import BaseScraper

BASE_URL = "https://sso.agc.gov.sg"
CURRENT_BROWSE_URL = "https://sso.agc.gov.sg/Browse/Act/Current/All?PageSize=20&SortBy=Title&SortOrder=ASC"

# Global variable for destination directory
DESTINATION_DIR = os.path.join(current_dir, '..', '..', '..', '..', 'data_ingestion', 'raw', 'sg', 'sso')

class SsoScraper(BaseScraper):
    def __init__(self):
        super().__init__()  # Initialize the base class (database connection)
        self.base_url = BASE_URL
        self.browse_url = CURRENT_BROWSE_URL

    def extract_documents_from_page(self, page_url):
        """Extract document information (title, PDF link) from a single page"""
        try:
            print(f"Processing page: {page_url}")
            html = getHtml(page_url)
            soup = BeautifulSoup(html, 'html.parser')
            
            documents = []
            
            # Look for table rows containing document information
            # Target the structure: <tr> containing both title and PDF download link
            rows = soup.find_all('tr', class_='')  # Empty class as shown in your example
            
            for row in rows:
                try:
                    # Extract title from the first <td> containing <a class="non-ajax">
                    title_cell = row.find('td')
                    if not title_cell:
                        continue
                    
                    title_link = title_cell.find('a', class_='non-ajax')
                    if not title_link:
                        continue
                    
                    title = title_link.get_text(strip=True)
                    
                    # Find PDF download link in the same row
                    # Look for links with 'ViewType=Pdf' in href and 'file-download' class
                    pdf_link = row.find('a', {
                        'class': lambda x: x and 'file-download' in x,
                        'href': lambda x: x and 'ViewType=Pdf' in x
                    })
                    
                    if pdf_link:
                        pdf_href = pdf_link['href']
                        
                        document = {
                            'title': title,
                            'pdf_href': pdf_href,
                        }
                        documents.append(document)
                        print(f"Found document: {title} | PDF: {pdf_href}")
                
                except Exception as e:
                    print(f"Error processing row: {str(e)}")
                    continue
            
            print(f"Found {len(documents)} documents on page: {page_url}")
            return documents
            
        except Exception as e:
            print(f"Error processing page {page_url}: {str(e)}")
            return []

    def download_pdf_file(self, pdf_link):
        """Download a single PDF file - handles SSO URLs by appending base URL"""
        try:
            print(f"Downloading PDF: {pdf_link}")
            
            parsed_url = urlparse(pdf_link)
            path_parts = [part for part in parsed_url.path.split('/') if part]
            
            if path_parts and 'ViewType=Pdf' in pdf_link:
                filename = f"{path_parts[-1]}.pdf"
            else:
                filename = os.path.basename(parsed_url.path)
                if not filename.endswith('.pdf'):
                    filename += '.pdf'
            
            # Handle cases where filename might be empty or just .pdf
            if not filename or filename == '.pdf':
                # Generate filename from URL path or timestamp
                if path_parts:
                    filename = f"{path_parts[-1]}.pdf"
                else:
                    filename = f"document_{int(time.time())}.pdf"
            
            # Create full destination path
            dest_path = os.path.join(DESTINATION_DIR, filename)
            
            # Avoid duplicate downloads
            if os.path.exists(dest_path):
                print(f"File already exists, skipping: {filename}")
                return dest_path
            
            # Download using the complete URL
            downloadPdf(pdf_link, dest_path)
            print(f"Downloaded: {filename}")
            return dest_path
            
        except Exception as e:
            print(f"Error downloading PDF {pdf_link}: {str(e)}")
            return None

    def get_next_page_url(self, soup, current_url):
        """Extract the next page URL from the current page - specifically for SSO pagination"""
        try:
            # Look for the specific SSO next page button pattern
            # Target: <a href="/Browse/Act/Current/All/1?PageSize=100&SortBy=Title&SortOrder=ASC" class="btn btn-default" aria-label="Next Page">
            next_button = soup.find('a', {
                'class': lambda x: x and 'btn' in x and 'btn-default' in x,
                'aria-label': 'Next Page'
            })
            
            if next_button and next_button.get('href'):
                next_url = urljoin(self.base_url, next_button['href'])
                print(f"Found next page button: {next_button['href']}")
                return next_url
            
            # Fallback: look for any link with "Next Page" aria-label
            next_link = soup.find('a', {'aria-label': 'Next Page'})
            if next_link and next_link.get('href'):
                next_url = urljoin(self.base_url, next_link['href'])
                print(f"Found next page link (fallback): {next_link['href']}")
                return next_url
            
            print("No next page button found")
            return None
            
        except Exception as e:
            print(f"Error finding next page URL: {str(e)}")
            return None

    def scrape(self, max_workers=10):
        """
        Scrape SSO documents with parallel processing
        max_workers: Number of concurrent threads to use
        """
        # Create destination directory if it doesn't exist
        os.makedirs(DESTINATION_DIR, exist_ok=True)
        
        all_documents = []
        current_url = self.browse_url
        page_count = 0
        
        print(f"Starting SSO scraping from: {current_url}")
        
        # Navigate through all pages to collect document information
        while current_url:
            try:
                page_count += 1
                print(f"\n=== Processing Page {page_count} ===")
                print(f"URL: {current_url}")
                
                html = getHtml(current_url)
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract document information from current page
                page_documents = self.extract_documents_from_page(current_url)
                all_documents.extend(page_documents)
                
                print(f"Page {page_count}: Found {len(page_documents)} documents")
                print(f"Total documents so far: {len(all_documents)}")
                
                # Find next page URL
                next_url = self.get_next_page_url(soup, current_url)
                
                if next_url and next_url != current_url:
                    current_url = next_url
                    print(f"Moving to next page: {next_url}")
                    # Add a small delay to be respectful to the server
                    time.sleep(1)
                else:
                    print("No more pages found or next button is disabled")
                    break
                    
            except Exception as e:
                print(f"Error processing page {current_url}: {str(e)}")
                break
        
        # Process documents to check for duplicates and collect information
        files_information = []
        all_pdf_links = set()
        filtered_count = 0
        
        print(f"\n=== Processing Documents ===")
        for doc in all_documents:
            try:
                title = doc['title']
                pdf_href = doc['pdf_href']
                
                # Convert relative URL to absolute URL
                full_pdf_url = urljoin(self.base_url, pdf_href) if pdf_href.startswith('/') else pdf_href

                # Check if document already exists in database
                if self._is_document_processed(full_pdf_url, title):
                    print(f"Document already processed, skipping: {title}")
                    filtered_count += 1
                    continue
                
                # Add to files information and PDF links for download
                files_information.append({
                    'url': full_pdf_url,
                    'timestamp': None,
                    'title': title
                })
                all_pdf_links.add(full_pdf_url)
                print(f"Processing document: {title}")
                
            except Exception as e:
                print(f"Error processing document {doc.get('title', 'Unknown')}: {str(e)}")
                filtered_count += 1
        
        # Download PDFs in parallel
        downloaded_files = []
        if all_pdf_links:
            print(f"\n=== Starting Parallel PDF Downloads ===")
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all PDF download tasks
                future_to_pdf = {
                    executor.submit(self.download_pdf_file, pdf_link): pdf_link 
                    for pdf_link in all_pdf_links
                }
                
                # Collect download results as they complete
                for future in as_completed(future_to_pdf):
                    pdf_link = future_to_pdf[future]
                    try:
                        result = future.result()
                        if result:
                            downloaded_files.append(result)
                    except Exception as e:
                        print(f"Error downloading {pdf_link}: {str(e)}")
        
        # Close database connection
        self.close_connection()
        
        return {
            'downloaded_files': downloaded_files,
            'files_information': files_information
        }
