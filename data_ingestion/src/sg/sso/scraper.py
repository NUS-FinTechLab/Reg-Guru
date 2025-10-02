import os
import sys
import time
import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# from common.base_scraper import BaseScraper
from common.helper import downloadPdftoS3, getHtml

# Add the parent directories to the Python path to resolve imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, src_dir)

from data_ingestion.src.common.BaseScraper import BaseScraper

BASE_URL = "https://sso.agc.gov.sg"
CURRENT_BROWSE_URL = "https://sso.agc.gov.sg/Browse/Act/Current/All?PageSize=500&SortBy=Title&SortOrder=ASC"

# Global variable for destination directory
DESTINATION_DIR = os.path.join(current_dir, '..', '..', '..', '..', 'data_ingestion', 'raw', 'sg', 'sso')
DESTINATION_KEY = "data_ingestion/raw/sg/sso"

# Sleep time
SLEEP_TIME = 0.5

class SsoScraper(BaseScraper):
    def __init__(self, ds_name, ds_code, ds_description):
        super().__init__(ds_name, ds_code, ds_description)  # Initialize the base class (database connection)
        self.base_url = BASE_URL
        self.browse_url = CURRENT_BROWSE_URL
        self.last_fetched_html = None
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.s3_obj = DESTINATION_KEY
    
    def extract_meta_from_webpage(self, weblink):
        """ Extract metadata from the document's webpage """
        time.sleep(SLEEP_TIME)
        html = getHtml(weblink)
        soup = BeautifulSoup(html, 'html.parser')
        desktop_timeline = soup.find('div', class_='desktop-timeline hidden-xs hidden-sm')
        latest_valid_date = desktop_timeline.find_all('div', class_='timestamp')[-1].find("a", class_=None).text.strip()  # class_=None avoids the file-download link
        latest_published_date = desktop_timeline.find_all('a', class_='timeline-popover')[-1]['data-date']

        return {'valid_date': latest_valid_date, 'published_date': latest_published_date}
    
    #### extract_documents_from_page should get doc_id (route), (pdf) url, weblink, title, published_date in documents.
    def extract_documents_from_page(self, page_url):
        """ Extract document information (title, PDF link) from a single page """
        print(f"Processing page: {page_url}")
        # Add delay to respect website policy (6 seconds between requests)
        time.sleep(SLEEP_TIME)
        try:
            html = getHtml(page_url)
            # Store HTML for reuse to avoid duplicate requests
            self.last_fetched_html = html
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for table rows containing document information            
            table = soup.find('table', class_="table browse-list")
            rows = table.find('tbody').find_all('tr')
        except Exception as e:
            print(f"Error fetching or parsing page {page_url}: {str(e)}")
            raise
        
        documents = []  
        for row in tqdm(rows):
            try:
                data_cells = row.find_all('td')
                # Extract title and route (as a unique identifier)
                title_cell = data_cells[0].find('a', class_="non-ajax")
                title = title_cell.get_text(strip=True)
                route = title_cell['href']
                # Extract PDF link
                pdf_href = data_cells[1].find('a', class_="non-ajax file-download")['href']
                if pdf_href:
                    # Extract other metadata
                    weblink = urljoin(self.base_url, route)
                    metadata = self.extract_meta_from_webpage(weblink)
                    document = {
                        'title': title,
                        'route': '_'.join(route.split('/')),
                        'weblink': weblink,
                        'pdf_href': urljoin(self.base_url, pdf_href) if pdf_href.startswith('/') else pdf_href,
                    }
                    document.update(metadata)
                    documents.append(document)
            
            except Exception as e:
                print(f"Error processing row: {str(e)}")
                continue
        
        print(f"Found {len(documents)} documents on page: {page_url}")
        return documents

    def get_next_page_url(self, soup):
        """ Extract the next page URL from the current page - specifically for SSO pagination """
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
            else:
                print("No next page button found")
                return None
            
        except Exception as e:
            print(f"Error finding next page URL: {str(e)}")
            return None
      
    def scrape(self):
        """ Scrape SSO documents """
        # Create destination directory if it doesn't exist
        os.makedirs(DESTINATION_DIR, exist_ok=True)
        
        all_documents = []
        current_url = self.browse_url
        page_count = 0
        
        print(f"Starting SSO scraping from: {current_url}")
        
        # Add initial delay to respect robots.txt crawl-delay
        print(f"Initial delay before first request ({SLEEP_TIME} seconds)...")
        time.sleep(SLEEP_TIME)

        # Navigate through all pages to collect document information
        while current_url:
            try:
                # For finding next page, we need to parse the same HTML that was already fetched
                # This avoids making another request
                print(f"URL: {current_url}")
                
                # Extract document information from current page (includes delay and HTML request)
                page_documents = self.extract_documents_from_page(current_url)
                all_documents.extend(page_documents)
                
                print(f"Page {page_count}: Found {len(page_documents)} documents")
                print(f"Total documents so far: {len(all_documents)}")
                
                html = self.last_fetched_html  # We'll modify extract_documents_from_page to store this
                if not html:
                    continue
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find next page URL
                next_url = self.get_next_page_url(soup)
                
                if next_url and next_url != current_url:
                    current_url = next_url
                    print(f"Moving to next page: {next_url}")
                    # Add delay to respect website policy (6 seconds between requests)
                    print(f"Waiting {SLEEP_TIME} seconds before next page request...")
                    time.sleep(SLEEP_TIME)
                else:
                    print("No more pages found or next button is disabled")
                    break
                    
            except Exception as e:
                print(f"Error processing page {current_url}: {str(e)}")
                break
        return all_documents
    
    def log_into_database(self, documents):
        """ Insert new documents into the database, update existing ones, and mark disappeared ones """
        self.db_client.connect()
        query = f"""CREATE TABLE IF NOT EXISTS bronze.feeds_{self.ds_code} (
            id SERIAL PRIMARY KEY,
            log_id INT NOT NULL REFERENCES logs.feeds(id) ON DELETE RESTRICT,
            title TEXT,
            pdf_url TEXT,
            weblink TEXT,
            doc_id TEXT NOT NULL,
            published_date TIMESTAMP,
            valid_date TIMESTAMP,
            inserted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            flag SMALLINT NOT NULL DEFAULT 0 REFERENCES ref.review_status(id),
            remark TEXT
        );"""
        self.db_client.execute(query)

        # Retrieve existing documents to avoid duplicates
        query = f"""SELECT DISTINCT ON (doc_id) doc_id, valid_date FROM bronze.feeds_{self.ds_code} WHERE flag = 0 ORDER BY doc_id, valid_date DESC"""
        result = self.db_client.execute(query)
        hist_df = pd.DataFrame([dict(row) for row in result])
        if not hist_df.empty:
            hist_df['valid_date'] = pd.to_datetime(hist_df['valid_date'], errors='raise').apply(lambda x: int(x.timestamp()) if pd.notnull(x) else None)
            docs = pd.DataFrame(documents).merge(hist_df, how='all', on='doc_id', suffixes=('', '_lastest'))
            
            # Documents need to be updated
            updated_docs = docs[docs['valid_date'] > docs['valid_date_latest']] # Need a module to handle updated docs, likely mark prev doc as obsolete and insert new doc as a record
            query = f"""UPDATE bronze.feeds_{self.ds_code} SET flag = 3, remark = 'Superseded by newer version' WHERE doc_id = %s AND flag = 0"""
            for _, doc in updated_docs.iterrows():
                try:
                    self.db_client.execute(query, (doc['doc_id'],))
                except Exception as e:
                    print(f"Error marking document {doc['doc_id']} as superseded: {str(e)}")

            # Documents that no longer exist
            disappeared_docs = docs[docs['valid_date'].isna()]
            query = f"""UPDATE bronze.feeds_{self.ds_code} SET flag = 2, remark = 'No longer available' WHERE doc_id = %s AND flag = 0"""
            for _, doc in disappeared_docs.iterrows():
                try:
                    self.db_client.execute(query, (doc['doc_id'],))
                except Exception as e:
                    print(f"Error marking document {doc['doc_id']} as disappeared: {str(e)}")
            
            # Insert new or updated documents
            docs_to_insert = docs[docs['valid_date'].notna() & (docs['valid_date'] > docs['valid_date_latest'].fillna(0))]
        else:
            print("No existing documents found, inserting all scraped documents.")
            docs_to_insert = pd.DataFrame(documents)
        
        if docs_to_insert.empty:
            print("No new or updated documents to insert.")
            self.db_client.close()
            return 0
        else:
            query = """INSERT INTO logs.feeds (source_id, remark, stage) VALUES (%s, %s, %s) RETURNING id;"""
            self.log_id = self.db_client.execute(query, (self.ds_id, self.ds_description, 1))[0][0]

            query = f"""
                INSERT INTO bronze.feeds_{self.ds_code} (log_id, title, pdf_url, weblink, doc_id, published_date, valid_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            values = [(self.log_id, doc['title'], doc['pdf_href'], doc['weblink'], doc['route'], doc['published_date'], doc['valid_date']) for _, doc in docs_to_insert.iterrows()]
            for value in values:
                try:
                    self.db_client.execute(query, value)
                except Exception as e:
                    print(f"[{self.log_id}] Error inserting {value[1]}: {e}")
                    query = """INSERT INTO logs.feeds (source_id, remark, stage) VALUES (%s, %s, %s);"""
                    self.db_client.execute(query, (self.ds_id, self.ds_description, 3))
                    raise

            query = """INSERT INTO logs.feeds (source_id, remark, stage) VALUES (%s, %s, %s);"""
            self.db_client.execute(query, (self.ds_id, self.ds_description, 2))
            query = f"SELECT COUNT(id) FROM bronze.feeds_{self.ds_code} WHERE log_id = {self.log_id}"
            new_entries_num = self.db_client.execute(query)
            print(f"{new_entries_num[0][0]} entries logged into database.")
            self.db_client.close()
            return new_entries_num[0][0]

    def store_documents(self, log_id):
        """ Download and store documents to S3 """
        self.db_client.connect()
        query = f"SELECT pdf_url, doc_id FROM bronze.feeds_{self.ds_code} WHERE log_id = {log_id}"
        new_entries = self.db_client.execute(query)
        self.db_client.close()
        if len(new_entries) > 0:
            new_feed_folder = self.s3_obj + '/' + str(log_id)
            for entry in new_entries:
                file_obj_key = new_feed_folder + '/' + entry['doc_id'] + ".pdf"  # sanitize filename
                try:
                    self.s3_client.store_pdf(entry['pdf_url'], self.bucket_name, file_obj_key)
                except Exception as e:
                    print(f"Error storing PDF {entry['pdf_url']}: {str(e)}")
                
            print(f"{len(new_entries)} documents uploaded to S3 {new_feed_folder}.")
        else:
            print("No new documents from this feed.")
        return

    def run(self):
        all_documents = self.scrape()
        new_entries_num = self.log_into_database(all_documents)
        self.store_documents(self.log_id)
        return new_entries_num

if __name__ == "__main__":
    scraper = SsoScraper(
        ds_name="sso acts",
        ds_code="sg",
        ds_description="Singapore Statutes Online official acts"
    )
    scraper.run()