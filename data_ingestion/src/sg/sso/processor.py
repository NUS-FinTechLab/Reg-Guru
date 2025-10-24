import io
import os
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd
import pdfplumber
from botocore.exceptions import ClientError
from dotenv import load_dotenv

from ...common.BaseProcessor import BaseProcessor

load_dotenv(override=True)


class SsoProcessor(BaseProcessor):
    """Transform raw SSO PDFs into cleaned text chunks ready for embedding."""

    DATASET_KEY = "data_ingestion/raw/sg/sso"

    def __init__(self, ds_code: str, batch_size: int = 12) -> None:
        super().__init__(ds_code, batch_size)
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.s3_obj = self.DATASET_KEY
        self.local_root = Path(__file__).resolve().parents[4] / self.DATASET_KEY

    # ---- Metadata preparation ----------------------------------------
    def clean_metadata(self, log_id: int) -> None:
        """Move raw bronze metadata to silver.metadata if not already done."""
        if self.check_if_metadata_cleaned(log_id):
            print(f"Metadata for log {log_id} already cleaned; skipping.")
            return

        self.db_client.connect()

        source_id = self.db_client.execute(
            "SELECT source_id FROM logs.feeds WHERE id = %s",
            (log_id,),
        )[0][0]

        rows = self.db_client.execute(
            f"SELECT * FROM bronze.feeds_{self.ds_code} WHERE log_id = %s",
            (log_id,),
        )
        records = [dict(row) for row in rows]
        if not records:
            self.db_client.close()
            print(f"No bronze records found for log {log_id}; nothing to clean.")
            return

        for record in records:
            self.db_client.execute(
                """
                    INSERT INTO silver.metadata (
                        id,
                        source_id,
                        log_id,
                        title,
                        weblink,
                        download_url,
                        published_date,
                        valid_date,
                        unique_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    record["id"],
                    source_id,
                    log_id,
                    record["title"],
                    record["weblink"],
                    record["pdf_url"],
                    record["published_date"],
                    record["valid_date"],
                    record["doc_id"],
                ),
            )

        self.db_client.close()
        print(f"Copied {len(records)} rows into silver.metadata for log {log_id}.")

    def extract_metadata(self, log_id: int) -> pd.DataFrame:
        """Load cleaned metadata so each PDF can be retrieved and processed."""
        self.db_client.connect()
        rows = self.db_client.execute(
            """
                SELECT title, download_url, published_date, valid_date, unique_id
                FROM silver.metadata
                WHERE log_id = %s
            """,
            (log_id,),
        )
        self.db_client.close()

        metadata = pd.DataFrame([dict(row) for row in rows])
        if metadata.empty:
            return metadata

        metadata["published_date"] = pd.to_datetime(
            metadata["published_date"], errors="coerce"
        ).apply(lambda ts: int(ts.timestamp()) if pd.notnull(ts) else None)
        metadata["valid_date"] = pd.to_datetime(
            metadata["valid_date"], errors="coerce"
        ).apply(lambda ts: int(ts.timestamp()) if pd.notnull(ts) else None)
        return metadata

    # ---- Text extraction ---------------------------------------------
    def _read_pdf_from_s3(self, key: str) -> bytes:
        """Download a PDF byte stream from S3."""
        try:
            response = self.s3_client.client.get_object(
                Bucket=self.bucket_name,
                Key=key,
            )
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code == "NoSuchKey":
                print(f"Missing S3 object for key {key}; skipping.")
                return b""
            raise

        return response["Body"].read()

    def _read_pdf_from_disk(self, path: Path) -> bytes:
        """Read a PDF that was stored locally during scraping."""
        return path.read_bytes()

    def extract_texts(self, key: str) -> List[str]:
        """Open a PDF (from S3 or disk) and return one entry per page."""
        if self.bucket_name:
            pdf_bytes = self._read_pdf_from_s3(key)
        else:
            relative_path = Path(key).relative_to(self.s3_obj)
            pdf_path = self.local_root / relative_path
            if not pdf_path.exists():
                print(f"Missing local PDF for key {key}; skipping.")
                return []
            pdf_bytes = self._read_pdf_from_disk(pdf_path)

        if not pdf_bytes:
            return []

        chunks: List[str] = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    chunks.append(text.strip())
        return chunks

    def _process_document(self, log_id: int, row: pd.Series) -> Dict[str, object]:
        key = f"{self.s3_obj}/{log_id}/{row['unique_id']}.pdf"
        # Pull the PDF, clean up its text page-by-page, and attach metadata.
        raw_pages = self.extract_texts(key)
        cleaned = self.clean_texts(raw_pages)
        if not cleaned:
            return {}

        return {
            "content": "\n".join(cleaned),
            "metadata": row.to_dict(),
        }

    # ---- Pipeline entrypoint ----------------------------------------
    def run(self, log_id: int) -> Iterable[List[Dict[str, object]]]:
        """Yield batches of processed documents ready for embedding."""
        # Step 1: ensure bronze rows are copied to the unified silver table.
        self.clean_metadata(log_id)
        # Step 2: fetch the metadata needed to locate every PDF.
        metadata = self.extract_metadata(log_id)
        if metadata.empty:
            print(f"No metadata available for log {log_id}; nothing to process.")
            return

        batch: List[Dict[str, object]] = []
        for _, row in metadata.iterrows():
            # Step 3: extract + clean the PDF text for this item.
            document = self._process_document(log_id, row)
            if not document:
                continue
            batch.append(document)
            if len(batch) == self.batch_size:
                yield batch
                batch = []

        if batch:
            yield batch
        print(f"Finished processing documents for log {log_id}.")
