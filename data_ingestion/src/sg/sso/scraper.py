import os
import time
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Dict, List, Optional



from ...common.BaseScraper import BaseScraper
from ...common.helper import downloadPdf, downloadPdftoS3, getHtml


class SsoScraper(BaseScraper):
    """Scraper for Singapore Statutes Online (SSO)."""

    BASE_URL = "https://sso.agc.gov.sg"
    BROWSE_URL = "https://sso.agc.gov.sg/Browse/Act/Current/All?PageSize=500&SortBy=Title&SortOrder=ASC"
    PAGE_DELAY = 6.0
    DOWNLOAD_DELAY = 6.0
    DATASET_KEY = "data_ingestion/raw/sg/sso"
    DATASET_DIR = Path(__file__).resolve().parents[4] / DATASET_KEY

    def __init__(self, ds_name, ds_code, ds_description, test_mode):
        super().__init__(ds_name, ds_code, ds_description, test_mode)
        self.s3_obj = self.DATASET_KEY

    # ---- HTML helpers -------------------------------------------------
    def _request_html(self, url: str) -> BeautifulSoup:
        """Fetch and parse a web page, pausing briefly between requests."""
        time.sleep(self.PAGE_DELAY)
        html = getHtml(url)
        return BeautifulSoup(html, "html.parser")

    def _extract_document_metadata(self, weblink: str) -> Dict[str, str]:
        """Load a statute detail page to capture publication and validity dates."""
        soup = self._request_html(weblink)
        timeline = soup.find("div", class_="desktop-timeline hidden-xs hidden-sm")
        # The timeline lists revisions; the last item is the most recent version.
        timestamps = timeline.find_all("div", class_="timestamp")
        latest_timestamp = timestamps[-1].find("a", class_=None).text.strip()
        latest_published = timeline.find_all("a", class_="timeline-popover")[-1]["data-date"]
        return {
            "valid_date": latest_timestamp,
            "published_date": latest_published,
        }

    def _extract_documents_from_page(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parse a table of acts and collect the essential fields for each row."""
        table = soup.find("table", class_="table browse-list")
        if not table:
            return []
        tbody = table.find("tbody")
        if not tbody:
            return []
        rows = tbody.find_all("tr")
        if self.test_mode:
            rows = rows[:2]

        documents: List[Dict[str, str]] = []
        for row in rows:
            # Each row lists a single act; extract its title, links, and metadata.
            cells = row.find_all("td")
            title_cell = cells[0].find("a", class_="non-ajax")
            pdf_cell = cells[1].find("a", class_="non-ajax file-download")
            if not title_cell or not pdf_cell:
                continue

            route = title_cell["href"]
            weblink = urljoin(self.BASE_URL, route)
            pdf_href = pdf_cell["href"]
            pdf_url = urljoin(self.BASE_URL, pdf_href)

            metadata = self._extract_document_metadata(weblink)
            documents.append(
                {
                    "title": title_cell.get_text(strip=True),
                    "route": "_".join(route.split("/")),
                    "weblink": weblink,
                    "pdf_href": pdf_url,
                    **metadata,
                }
            )

        return documents

    def _next_page_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Locate the "Next Page" button in the paginator."""
        next_button = soup.find("a", attrs={"aria-label": "Next Page"})
        if next_button and next_button.get("href"):
            return urljoin(self.BASE_URL, next_button["href"])
        return None

    # ---- Public interface --------------------------------------------
    def scrape(self) -> List[Dict[str, str]]:
        """Iterate through the browse pages and collect document metadata."""
        self.DATASET_DIR.mkdir(parents=True, exist_ok=True)

        all_documents: List[Dict[str, str]] = []
        current_url = self.BROWSE_URL

        while current_url:
            # Step 1: fetch the listing page and capture every document row.
            soup = self._request_html(current_url)
            page_documents = self._extract_documents_from_page(soup)
            all_documents.extend(page_documents)

            if self.test_mode: # test
                break

            # Step 2: follow the paginator until there are no more pages.
            next_url = self._next_page_url(soup)
            if not next_url or next_url == current_url:
                break
            current_url = next_url

        print(f"Collected {len(all_documents)} SSO documents from browse pages.")
        return all_documents

    def log_into_database(self, documents: List[Dict[str, str]]) -> int:
        """Insert new documents and return the number of records stored."""
        if not documents:
            print("No documents were scraped; nothing to log.")
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
                    valid_date TIMESTAMP,
                    inserted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    flag SMALLINT NOT NULL DEFAULT 0 REFERENCES ref.review_status(id),
                    remark TEXT
                );
            """
        )

        history_query = f"""
                SELECT DISTINCT ON (doc_id)
                    doc_id,
                    valid_date
                FROM bronze.feeds_{self.ds_name}
                WHERE flag = 0
                ORDER BY doc_id, valid_date DESC;
            """
        history_rows = self.db_client.execute(history_query)
        history = pd.DataFrame([dict(row) for row in history_rows])

        documents_df = pd.DataFrame(documents)
        documents_df["valid_date"] = pd.to_datetime(
            documents_df["valid_date"], errors="coerce"
        )
        documents_df["published_date"] = pd.to_datetime(
            documents_df["published_date"], errors="coerce"
        )
        if history.empty:
            # First run: insert everything we just scraped.
            records_to_insert = documents_df
        else:
            print("Check existing documents for newer versions.")
            history["valid_date"] = pd.to_datetime(history["valid_date"])
            merged = documents_df.merge(
                history, how="outer", left_on="route", right_on="doc_id", suffixes=("", "_latest")
            )
            # Mark older versions of the same document as superseded.
            superseded = merged[merged["valid_date"] > merged["valid_date_latest"]]
            for doc_id in superseded["doc_id"].unique():
                self.db_client.execute(
                    f"""
                        UPDATE bronze.feeds_{self.ds_name}
                        SET flag = 3, remark = 'Superseded by newer version'
                        WHERE doc_id = %s AND flag = 0;
                    """,
                    (doc_id,),
                )
                self.db_client.execute(
                    f"""
                        UPDATE {self.metadata_table}
                        SET flag = 3, remark = 'Superseded by newer version'
                        WHERE unique_id = %s AND flag = 0;
                    """,
                    (doc_id,),
                )
            # If a doc vanished from the listing, flag it as no longer available.
            missing = merged[merged["valid_date"].isna()]
            for doc_id in missing["doc_id"].unique():
                self.db_client.execute(
                    f"""
                        UPDATE bronze.feeds_{self.ds_name}
                        SET flag = 2, remark = 'No longer available'
                        WHERE doc_id = %s AND flag = 0;
                    """,
                    (doc_id,),
                )
                self.db_client.execute(
                    f"""
                        UPDATE {self.metadata_table}
                        SET flag = 2, remark = 'No longer available'
                        WHERE unique_id = %s AND flag = 0;
                    """,
                    (doc_id,),
                )
            records_to_insert = merged[merged["valid_date"].notna()]
            records_to_insert = records_to_insert[
                records_to_insert["valid_date"]
                > records_to_insert["valid_date_latest"].fillna(pd.Timestamp.min)
            ]

        if records_to_insert.empty:
            self.db_client.close()
            print("No new SSO records to insert into bronze.")
            return 0

        # Every ingestion run gets its own log id so downstream steps can find the PDFs.
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
                published_date,
                valid_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        for _, record in records_to_insert.iterrows():
            self.db_client.execute(
                insert_query,
                (
                    self.log_id,
                    record["title"],
                    record["pdf_href"],
                    record["weblink"],
                    record["route"],
                    record["published_date"],
                    record["valid_date"],
                ),
            )

        count = self.db_client.execute(
            f"SELECT COUNT(id) FROM bronze.feeds_{self.ds_name} WHERE log_id = %s",
            (self.log_id,),
        )[0][0]

        self.db_client.close()
        print(f"Logged {count} SSO records with log id {self.log_id}.")
        return count

    def store_documents(self, log_id: Optional[int]) -> None:
        """Persist scraped PDFs either locally or on S3."""
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
            print("No documents associated with the supplied log id.")
            return

        bucket_name = os.getenv("S3_BUCKET_NAME")
        feed_prefix = f"{self.s3_obj}/{log_id}"
        referer = self.BASE_URL

        for row in rows:
            doc_id = row["doc_id"]
            pdf_url = row["pdf_url"]
            # Store each PDF either under the configured bucket or the local raw folder.
            if bucket_name:
                try:
                    downloadPdftoS3(
                        pdf_url,
                        f"{feed_prefix}/{doc_id}.pdf",
                        referer=referer,
                    )
                except Exception as exc:
                    print(f"Failed to upload {pdf_url} → S3: {exc}")
            else:
                target_dir = self.DATASET_DIR / str(log_id)
                target_dir.mkdir(parents=True, exist_ok=True)
                try:
                    downloadPdf(
                        pdf_url,
                        target_dir / f"{doc_id}.pdf",
                        referer=referer,
                    )
                except Exception as exc:
                    print(f"Failed to download {pdf_url}: {exc}")

            time.sleep(self.DOWNLOAD_DELAY)

        destination = bucket_name or str(self.DATASET_DIR)
        print(f"Stored {len(rows)} SSO documents under {destination}.")

    def run(self) -> int:
        """Full scraper execution: scrape, log, and persist PDFs."""
        documents = self.scrape()
        inserted_count = self.log_into_database(documents)
        # Downstream stages rely on the PDFs being accessible by log id.
        self.store_documents(self.log_id)
        return inserted_count


# if __name__ == "__main__":
#     scraper = SsoScraper(
#         ds_name="sg_sso",
#         ds_code="sg",
#         ds_description="Singapore Statutes Online official acts"
#     )
#     scraper.run()
