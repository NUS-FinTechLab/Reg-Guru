import os
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import pandas as pd
from bs4 import BeautifulSoup

from ...common.BaseScraper import BaseScraper
from ...common.helper import downloadPdf, downloadPdftoS3, getHtml


class FincenScraper(BaseScraper):
    """Scraper for FinCEN advisories and bulletins."""

    BASE_URL = "https://www.fincen.gov"
    LISTING_URL = (
        "https://www.fincen.gov/resources/advisoriesbulletinsfact-sheets/advisories"
    )
    PAGE_DELAY = 0.5
    DATASET_KEY = "data_ingestion/raw/us/fincen"
    DATASET_DIR = Path(__file__).resolve().parents[4] / DATASET_KEY

    def __init__(self, ds_name, ds_code, ds_description, test_mode):
        super().__init__(ds_name, ds_code, ds_description, test_mode)
        self.s3_obj = self.DATASET_KEY

    # ---- HTML helpers -------------------------------------------------
    def _request_html(self, url: str) -> BeautifulSoup:
        """Fetch and parse a web page, respecting a short delay between calls."""
        time.sleep(self.PAGE_DELAY)
        html = getHtml(url)
        return BeautifulSoup(html, "html.parser")

    def _listing_links(self, soup: BeautifulSoup) -> List[str]:
        """Collect advisory detail page links from a listing page."""
        links: List[str] = []
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            if "/resources/advisories/" not in href:
                continue
            links.append(urljoin(self.BASE_URL, href))
            if self.test_mode and len(links) >= 2:
                break
        return links

    def _parse_detail_page(self, detail_url: str) -> Optional[Dict[str, str]]:
        """Extract advisory metadata and the primary PDF link."""
        soup = self._request_html(detail_url)

        title = "FinCEN Advisory"
        subject_field = soup.find("div", class_="field--name-field-advisory-subject")
        if subject_field:
            item = subject_field.find("div", class_="field__item")
            if item:
                extracted_title = item.get_text(strip=True)
                if extracted_title:
                    title = extracted_title

        time_tag = soup.find("time")
        datetime_value = time_tag.get("datetime") if time_tag else None

        pdf_url: Optional[str] = None
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            if href.lower().endswith(".pdf"):
                pdf_url = urljoin(self.BASE_URL, href)
                break

        if not pdf_url:
            return None

        doc_id = self._generate_doc_id(detail_url, pdf_url)
        return {
            "title": title,
            "weblink": detail_url,
            "pdf_url": pdf_url,
            "doc_id": doc_id,
            "published_date": datetime_value,
        }

    def _generate_doc_id(self, detail_url: str, pdf_url: str) -> str:
        """Create a deterministic identifier for the advisory PDF."""
        parsed_detail = urlparse(detail_url)
        route = "_".join(filter(None, parsed_detail.path.split("/"))) or "advisory"
        parsed_pdf = urlparse(pdf_url)
        filename = Path(parsed_pdf.path).stem or "document"
        slug = f"{route}_{filename}".replace("-", "_").replace(" ", "_")
        return slug.lower()

    def _next_page_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Find the URL for the next listing page, if one exists."""
        next_button = soup.find("a", class_="usa-pagination__next-page")
        if next_button and next_button.get("href"):
            return urljoin(self.LISTING_URL, next_button["href"])
        return None

    # ---- Public interface --------------------------------------------
    def scrape(self) -> List[Dict[str, str]]:
        """Traverse listing pages and collect advisory metadata."""
        self.DATASET_DIR.mkdir(parents=True, exist_ok=True)

        collected: List[Dict[str, str]] = []
        seen_links = set()
        current_url = self.LISTING_URL

        while current_url:
            # Step 1: load the current listing page.
            soup = self._request_html(current_url)
            # Step 2: visit each unseen advisory detail page and capture metadata.
            for detail_url in self._listing_links(soup):
                if detail_url in seen_links:
                    continue
                seen_links.add(detail_url)
                metadata = self._parse_detail_page(detail_url)
                if metadata:
                    collected.append(metadata)
            if self.test_mode: # test
                break

            # Step 3: follow the paginator until no further pages are available.
            next_url = self._next_page_url(soup)
            if not next_url or next_url == current_url:
                break
            current_url = next_url

        print(f"Collected {len(collected)} FinCEN advisories from listings.")
        return collected

    def log_into_database(self, documents: List[Dict[str, str]]) -> int:
        """Insert new advisory metadata into bronze feeds."""
        if not documents:
            print("No FinCEN advisories were scraped; nothing to log.")
            return 0

        self.db_client.connect()
        self.db_client.execute(
            f"""
                CREATE TABLE IF NOT EXISTS bronze.feeds_{self.ds_name} (
                    id SERIAL PRIMARY KEY,
                    log_id INT NOT NULL REFERENCES logs.feeds(id) ON DELETE RESTRICT,
                    title TEXT,
                    pdf_url TEXT,
                    weblink TEXT,
                    doc_id TEXT NOT NULL,
                    published_date TIMESTAMP,
                    inserted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    flag SMALLINT NOT NULL DEFAULT 0 REFERENCES ref.review_status(id),
                    remark TEXT
                );
            """
        )

        # Look up existing advisory ids so we only insert new records.
        history_rows = self.db_client.execute(
            f"SELECT doc_id FROM bronze.feeds_{self.ds_name} WHERE flag = 0;"
        )
        existing_doc_ids = {row["doc_id"] for row in history_rows}

        documents_df = pd.DataFrame(documents).drop_duplicates(subset="doc_id")
        documents_df["published_date"] = pd.to_datetime(
            documents_df["published_date"], errors="coerce"
        )

        # Keep only advisories that have not been seen before.
        records_to_insert = documents_df[~documents_df["doc_id"].isin(existing_doc_ids)]

        if records_to_insert.empty:
            self.db_client.close()
            print("No new FinCEN advisories to insert into bronze.")
            return 0

        self.log_id = self.db_client.execute(
            """
                INSERT INTO logs.feeds (source_id, remark, stage)
                VALUES (%s, %s, %s)
                RETURNING id;
            """,
            (self.ds_id, self.ds_description, 1),
        )[0][0]

        insert_query = f"""
            INSERT INTO bronze.feeds_{self.ds_name} (
                log_id,
                title,
                pdf_url,
                weblink,
                doc_id,
                published_date
            )
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        for _, record in records_to_insert.iterrows():
            published = (
                record["published_date"].to_pydatetime()
                if pd.notnull(record["published_date"])
                else None
            )
            self.db_client.execute(
                insert_query,
                (
                    self.log_id,
                    record["title"],
                    record["pdf_url"],
                    record["weblink"],
                    record["doc_id"],
                    published,
                ),
            )

        count = self.db_client.execute(
            f"SELECT COUNT(id) FROM bronze.feeds_{self.ds_name} WHERE log_id = %s",
            (self.log_id,),
        )[0][0]

        self.db_client.close()
        print(f"Logged {count} FinCEN advisories with log id {self.log_id}.")
        return count

    def store_documents(self, log_id: Optional[int]) -> None:
        """Download PDFs for the advisories recorded in this run."""
        if not log_id:
            print("No log id available; skipping document storage.")
            return

        self.db_client.connect()
        rows = self.db_client.execute(
            f"SELECT pdf_url, doc_id FROM bronze.feeds_{self.ds_name} WHERE log_id = %s",
            (log_id,),
        )
        self.db_client.close()

        if not rows:
            print("No FinCEN advisories associated with the supplied log id.")
            return

        bucket_name = os.getenv("S3_BUCKET_NAME")
        feed_prefix = f"{self.s3_obj}/{log_id}"

        for row in rows:
            doc_id = row["doc_id"]
            pdf_url = row["pdf_url"]
            if bucket_name:
                try:
                    downloadPdftoS3(pdf_url, f"{feed_prefix}/{doc_id}.pdf")
                except Exception as exc:
                    print(f"Failed to upload {pdf_url} → S3: {exc}")
            else:
                target_dir = self.DATASET_DIR / str(log_id)
                target_dir.mkdir(parents=True, exist_ok=True)
                try:
                    downloadPdf(pdf_url, target_dir / f"{doc_id}.pdf")
                except Exception as exc:
                    print(f"Failed to download {pdf_url}: {exc}")

        destination = bucket_name or str(self.DATASET_DIR)
        print(f"Stored {len(rows)} FinCEN advisories under {destination}.")

    def run(self) -> int:
        """Full scraper execution: scrape, log, and persist PDFs."""
        documents = self.scrape()
        inserted_count = self.log_into_database(documents)
        self.store_documents(self.log_id)
        return inserted_count
