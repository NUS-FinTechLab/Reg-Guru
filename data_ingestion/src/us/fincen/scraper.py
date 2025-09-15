from bs4 import BeautifulSoup
import sys
import os
from urllib.parse import urlparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directories to the Python path to resolve imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, src_dir)

from common.helper import downloadPdf, getHtml, getPdfLinks, feed_exists_pg

BASE_URL = "https://www.fincen.gov"
ADVISORY_URL = "https://www.fincen.gov/resources/advisoriesbulletinsfact-sheets/advisories"

# Global variable for destination directory
DESTINATION_DIR = os.path.join(current_dir, '..', '..', '..', '..', 'data_ingestion', 'raw', 'us', 'fincen')

class FincenScraper:
    def __init__(self):
        self.baseUrl = BASE_URL
        self.advisoryUrl = ADVISORY_URL
        self.db_conn = None
        self._setup_database_connection()
    
    def _setup_database_connection(self):
        """Set up database connection using environment variables"""
        try:
            self.db_conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                dbname=os.getenv("DB_NAME")
            )
            print(f"Connected to PostgreSQL database for duplicate checking")
        except Exception as e:
            print(f"Warning: Could not connect to database: {str(e)}")
            print("Proceeding without duplicate filtering...")
    
    def _is_document_processed(self, url, title):
        """Check if document already exists in database"""
        if not self.db_conn:
            return False
        try:
            return feed_exists_pg(self.db_conn, url, title)
        except Exception as e:
            print(f"Warning: Error checking database: {str(e)}")
            return False
    
    def datetime_to_timestamp(self, datetime_str):
        """Convert ISO datetime string to timestamp"""
        if not datetime_str:
            return None
        try:
            # Handle the 'Z' timezone indicator
            if datetime_str.endswith('Z'):
                datetime_str = datetime_str.replace('Z', '+00:00')
            dt = datetime.fromisoformat(datetime_str)
            return dt.timestamp()
        except (ValueError, AttributeError):
            return None
    
    def process_advisory_link(self, link):
        """Process a single advisory link to extract metadata and PDF links"""
        try:
            print(f"Processing advisory: {link}")
            html = getHtml(link)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Get the metadata (year, title) first for duplicate checking
            timeTag = soup.find("time")
            
            subjectField = soup.find("div", class_="field--name-field-advisory-subject")
            title = 'N/A'
            if subjectField:
                items = subjectField.find_all("div", class_="field__item")
                if items:
                    title = items[0].get_text(strip=True)
            
            # Extract datetime attribute from time tag
            datetime_value = timeTag.get('datetime') if timeTag else None
            timestamp = self.datetime_to_timestamp(datetime_value)
            
            # Check if document already exists in database before processing PDF links
            if self._is_document_processed(link, title):
                print(f"Document already processed, skipping: {title}")
                return None
            
            # Get only the first PDF link on the page
            first_pdf_link = None
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.lower().endswith('.pdf'):
                    first_pdf_link = href
                    break  # Only take the first PDF link found
            
            print(f"Processed: {datetime_value}, {title}, Timestamp: {timestamp}")
            
            # Convert relative PDF link to absolute URL (only if PDF link exists)
            absolute_pdf_links = []
            if first_pdf_link:
                absolute_pdf_link = self.baseUrl + first_pdf_link if first_pdf_link.startswith('/') else first_pdf_link
                absolute_pdf_links = [absolute_pdf_link]
            
            return {
                'url': link,
                'timestamp': timestamp,
                'title': title,
                'pdf_links': absolute_pdf_links,
                'datetime_value': datetime_value
            }
            
        except Exception as e:
            print(f"Error processing advisory {link}: {str(e)}")
            return None
    
    def download_pdf_file(self, pdf_link):
        """Download a single PDF file"""
        try:
            print(f"Downloading PDF: {pdf_link}")
            # Extract filename from URL
            parsed_url = urlparse(pdf_link)
            filename = os.path.basename(parsed_url.path)
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            # Create full destination path
            dest_path = os.path.join(DESTINATION_DIR, filename)
            downloadPdf(pdf_link, dest_path)
            print(f"Downloaded: {filename}")
            return dest_path
            
        except Exception as e:
            print(f"Error downloading PDF {pdf_link}: {str(e)}")
            return None
    
    def close_connection(self):
        """Close database connection"""
        if self.db_conn:
            try:
                self.db_conn.close()
                print("Database connection closed")
            except Exception as e:
                print(f"Error closing database connection: {str(e)}")

    def scrape(self, max_workers=10):
        """
        Scrape FinCEN advisories with parallel processing
        max_workers: Number of concurrent threads to use
        """
        html = getHtml(self.advisoryUrl)
        soup = BeautifulSoup(html, 'html.parser')
        
        advisoryLinks = set()
        current_url = self.advisoryUrl

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
        
        print(f"Found {len(advisoryLinks)} advisory links to process")
        
        # Create destination directory if it doesn't exist
        os.makedirs(DESTINATION_DIR, exist_ok=True)
        
        files_information = []
        all_pdf_links = set()
        filtered_count = 0
        
        # Process advisory links in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all advisory processing tasks
            future_to_link = {
                executor.submit(self.process_advisory_link, link): link 
                for link in advisoryLinks
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_link):
                link = future_to_link[future]
                try:
                    result = future.result()
                    if result:  # Only process non-None results (not filtered duplicates)
                        files_information.append({
                            'url': result['url'],
                            'timestamp': result['timestamp'],
                            'title': result['title']
                        })
                        # Collect all PDF links for downloading
                        all_pdf_links.update(result['pdf_links'])
                    else:
                        filtered_count += 1  # Count filtered duplicates
                except Exception as e:
                    print(f"Error processing {link}: {str(e)}")
        
        
        # Download PDFs in parallel
        downloaded_files = []
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
        
        print(f"Successfully downloaded {len(downloaded_files)} PDF files")
        
        # Close database connection
        self.close_connection()
        
        # Print final summary
        print(f"\n=== Scraping Summary ===")
        print(f"Total advisories found: {len(advisoryLinks)}")
        print(f"Duplicate documents filtered: {filtered_count}")
        print(f"New documents to process: {len(files_information)}")
        print(f"PDF files downloaded: {len(downloaded_files)}")
        
        # Combine downloaded files and files information into a single dictionary
        return {
            'downloaded_files': downloaded_files,
            'files_information': files_information
        }
