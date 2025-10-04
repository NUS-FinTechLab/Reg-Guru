import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from hashlib import sha256
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ...common import BaseScraper
from ...common.helper import downloadPdf, downloadPdftoS3, getHtml

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_URL = "https://www.fincen.gov"
ADVISORY_URL = (
    "https://www.fincen.gov/resources/advisoriesbulletinsfact-sheets/advisories"
)

# Storage targets
DESTINATION_DIR = os.path.join(
    CURRENT_DIR, "..", "..", "..", "..", "data_ingestion", "raw", "us", "fincen"
)
DESTINATION_KEY = "data_ingestion/raw/us/fincen"


class FincenScraper(BaseScraper):
    DEFAULT_DS_NAME = "fincen"
    DEFAULT_DS_CODE = "us"
    DEFAULT_DS_DESCRIPTION = "FinCEN Advisories and Bulletins"

    def __init__(
        self,
        ds_name=DEFAULT_DS_NAME,
        ds_code=DEFAULT_DS_CODE,
        ds_description=DEFAULT_DS_DESCRIPTION,
    ):
        super().__init__(ds_name, ds_code, ds_description)
        self.baseUrl = BASE_URL
        self.advisoryUrl = ADVISORY_URL
        self.s3_obj = DESTINATION_KEY

    def datetime_to_timestamp(self, datetime_str):
        """Convert ISO datetime string to timestamp"""
        if not datetime_str:
            return None
        try:
            # Handle the 'Z' timezone indicator
            if datetime_str.endswith("Z"):
                datetime_str = datetime_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(datetime_str)
            return dt.timestamp()
        except (ValueError, AttributeError):
            return None

    def process_advisory_link(self, link):
        """Process a single advisory link to extract metadata and PDF links"""
        try:
            print(f"Processing advisory: {link}")
            html = getHtml(link)
            soup = BeautifulSoup(html, "html.parser")

            # Get the metadata (year, title) first for duplicate checking
            timeTag = soup.find("time")

            subjectField = soup.find("div", class_="field--name-field-advisory-subject")
            title = "N/A"
            if subjectField:
                items = subjectField.find_all("div", class_="field__item")
                if items:
                    title = items[0].get_text(strip=True)

            # Extract datetime attribute from time tag
            datetime_value = timeTag.get("datetime") if timeTag else None
            timestamp = self.datetime_to_timestamp(datetime_value)

            if self._is_recorded_in_database(link, title):
                print(f"Document already recorded in database, skipping: {title}")
                return None

            # Get only the first PDF link on the page
            first_pdf_link = None
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.lower().endswith(".pdf"):
                    first_pdf_link = href
                    break  # Only take the first PDF link found

            print(f"Processed: {datetime_value}, {title}, Timestamp: {timestamp}")

            # Convert relative PDF link to absolute URL (only if PDF link exists)
            absolute_pdf_links = []
            if first_pdf_link:
                absolute_pdf_link = (
                    self.baseUrl + first_pdf_link
                    if first_pdf_link.startswith("/")
                    else first_pdf_link
                )
                absolute_pdf_links = [absolute_pdf_link]

            return {
                "url": link,
                "timestamp": timestamp,
                "title": title,
                "pdf_links": absolute_pdf_links,
                "datetime_value": datetime_value,
            }

        except Exception as e:
            print(f"Error processing advisory {link}: {str(e)}")
            return None

    def scrape(self, run_id=None, max_workers=10):
        """
        Scrape FinCEN advisories with parallel processing.
        max_workers: Number of concurrent threads to use.
        """
        print("🌐 Fetching FinCEN advisory page...")
        try:
            if run_id is None:
                run_id = datetime.utcnow().strftime("%Y%m%d%H%M%S")

            html = getHtml(self.advisoryUrl)
            soup = BeautifulSoup(html, "html.parser")

            advisoryLinks = set()
            current_url = self.advisoryUrl
            page_count = 0

            # Process all pages starting with the base URL
            while True:
                page_count += 1
                print(f"📄 Processing page {page_count}: {current_url}")

                # Get all links to responding advisory resources page
                links = soup.find_all("a", href=True)

                # Filter links that point to advisory resources
                links = [a["href"] for a in links if "/resources/advisories/" in a["href"]]
                links = [
                    self.baseUrl + link if link.startswith("/") else link for link in links
                ]
                advisoryLinks.update(links)
                print(f"  📎 Found {len(links)} advisory links on this page")

                # Look for the next page link
                next_link = soup.find("a", class_="usa-pagination__next-page")
                if not next_link:
                    break

                # Get the next page
                current_url = self.advisoryUrl + next_link["href"]
                html = getHtml(current_url)
                soup = BeautifulSoup(html, "html.parser")

            print(f"Found {len(advisoryLinks)} advisory links to process")

            documents = []
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
                        if not result:
                            filtered_count += 1  # Count filtered duplicates
                            continue

                        for pdf_link in result["pdf_links"]:
                            doc_id = self._generate_doc_id(result["url"], pdf_link)
                            storage = self._store_document(pdf_link, run_id, doc_id)
                            if not storage:
                                continue

                            documents.append(
                                {
                                    "url": result["url"],
                                    "timestamp": result["timestamp"],
                                    "title": result["title"],
                                    "doc_id": doc_id,
                                    "pdf_url": pdf_link,
                                    "storage": storage,
                                    "datetime_value": result["datetime_value"],
                                }
                            )
                    except Exception as e:
                        print(f"Error processing {link}: {str(e)}")

            print(f"Successfully captured {len(documents)} advisory documents")

            # Print final summary
            print(f"\n=== Scraping Summary ===")
            print(f"Total advisories found: {len(advisoryLinks)}")
            print(f"Duplicate documents filtered: {filtered_count}")
            print(f"New documents to process: {len(documents)}")

            # Combine downloaded files and files information into a single dictionary
            return {
                "documents": documents,
                "run_id": run_id,
            }
        finally:
            self.close_connection()

    def _is_recorded_in_database(self, link, title):
        try:
            self.db_client.connect()
            query = (
                "SELECT 1 FROM bronze.feeds_us "
                "WHERE url = %s AND title = %s LIMIT 1"
            )
            result = self.db_client.execute(query, (link, title or "N/A"))
            return bool(result)
        except Exception as e:
            print(
                f"Warning: Unable to verify existing FinCEN record for {link}: {str(e)}"
            )
            return False

    def _generate_doc_id(self, link, pdf_link):
        parsed_link = urlparse(link)
        path_slug = "_".join(filter(None, parsed_link.path.split("/")))
        if not path_slug:
            path_slug = "advisory"

        parsed_pdf = urlparse(pdf_link)
        filename = os.path.basename(parsed_pdf.path) or "document.pdf"
        name_part = os.path.splitext(filename)[0]
        slug = f"{path_slug}_{name_part}".replace("-", "_").replace(" ", "_")

        digest = sha256(pdf_link.encode("utf-8")).hexdigest()[:10]
        return f"{slug}_{digest}".lower()

    def _store_document(self, pdf_url, run_id, doc_id):
        bucket_name = os.getenv("S3_BUCKET_NAME")
        if bucket_name:
            object_key = f"{DESTINATION_KEY}/{run_id}/{doc_id}.pdf"
            try:
                downloadPdftoS3(pdf_url, object_key)
                return {"type": "s3", "bucket": bucket_name, "key": object_key}
            except Exception as e:
                print(f"Error uploading PDF {pdf_url} to S3: {str(e)}")
                return None

        local_dir = os.path.join(DESTINATION_DIR, run_id)
        os.makedirs(local_dir, exist_ok=True)
        dest_path = os.path.join(local_dir, f"{doc_id}.pdf")
        try:
            downloadPdf(pdf_url, dest_path)
            return {"type": "local", "path": dest_path}
        except Exception as e:
            print(f"Error saving PDF {pdf_url} locally: {str(e)}")
            return None

    def log_into_database(self, **kwargs):
        """FinCEN scraper currently skips database logging."""
        return 0

    def store_documents(self, log_id, **kwargs):
        """FinCEN scraper leaves downstream storage to the processor stage."""
        return None

    def run(self, **kwargs):
        return self.scrape(**kwargs)
