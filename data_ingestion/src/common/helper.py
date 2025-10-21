import os
import sqlite3
import time
from typing import Optional

import boto3
import psycopg2
import requests
from bs4 import BeautifulSoup
from botocore.exceptions import ClientError


def getHtml(url):
    r"""Sends a GET request."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=50)
    response.raise_for_status()

    return response.text


def getPdfLinks(url):
    r"""Extracts all PDF links from a given URL."""
    html = getHtml(url)
    soup = BeautifulSoup(html, "html.parser")

    pdfLinks = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".pdf"):
            pdfLinks.add(href)

    return pdfLinks


_BASE_PDF_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}


def _build_pdf_headers(referer: Optional[str] = None) -> dict:
    headers = dict(_BASE_PDF_HEADERS)
    if referer:
        headers["Referer"] = referer
    return headers


def _fetch_pdf_bytes(
    url: str,
    *,
    referer: Optional[str] = None,
    timeout: tuple = (10, 30),
    max_retries: int = 3,
) -> bytes:
    """Download PDF content with retry/backoff to handle intermittent 4xx/5xx."""

    session = requests.Session()
    for attempt in range(max_retries):
        try:
            response = session.get(
                url,
                headers=_build_pdf_headers(referer),
                stream=True,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.content
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "?"
            if status in {429, 467, 503} and attempt < max_retries - 1:
                time.sleep(2**attempt)
                continue
            raise RuntimeError(f"HTTP {status} while downloading {url}") from exc
        except requests.RequestException as exc:
            if attempt < max_retries - 1:
                time.sleep(2**attempt)
                continue
            raise RuntimeError(f"Error downloading {url}: {exc}") from exc

    raise RuntimeError(f"Exceeded retries downloading {url}")


def downloadPdf(url, dest_path, *, referer: Optional[str] = None) -> None:
    """Downloads a PDF from a given URL to the specified destination path."""

    pdf_bytes = _fetch_pdf_bytes(url, referer=referer)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_bytes(pdf_bytes)


def downloadPdftoS3(url, dest_key, *, referer: Optional[str] = None) -> None:
    """Puts a PDF from a given URL as an S3 object specified by the object key."""

    bucket_name = os.getenv("S3_BUCKET_NAME")
    if not bucket_name:
        raise ValueError("S3_BUCKET_NAME is not configured; cannot upload to S3.")

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION"),
    )

    try:
        pdf_bytes = _fetch_pdf_bytes(url, referer=referer)
        s3_client.put_object(
            Bucket=bucket_name,
            Key=dest_key,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )
    except ClientError as exc:
        raise RuntimeError(f"S3 upload failed for {dest_key}: {exc}") from exc


# PostgreSQL-compatible helper functions
def feed_exists_pg(conn, url, title, region="us"):
    r"""Checks if a feed with the same URL and title already exists in the PostgreSQL database.

    Args:
        conn: PostgreSQL database connection
        url: The URL to check
        title: The title to check
        region: The region code (us, sg, eu) to determine which feeds table to query

    Returns:
        bool: True if feed exists, False otherwise
    """
    table_name = f"bronze.feeds_{region}"
    sql = f""" SELECT COUNT(*) FROM {table_name} 
              WHERE url = %s AND title = %s """
    cur = conn.cursor()
    cur.execute(sql, (url, title))
    count = cur.fetchone()[0]
    return count > 0


def insert_feed_pg(conn, feed, region="us"):
    r"""Inserts a feed record into the PostgreSQL database.

    Args:
        conn: PostgreSQL database connection
        feed: Tuple containing (id, url, timestamp, title, inserted_at)
        region: The region code (us, sg, eu) to determine which feeds table to insert into

    Returns:
        int: Number of rows affected
    """
    table_name = f"bronze.feeds_{region}"
    sql = f""" INSERT INTO {table_name}(id, url, timestamp, title, inserted_at)
              VALUES(%s,%s,%s,%s,%s) """
    cur = conn.cursor()
    cur.execute(sql, feed)
    conn.commit()
    return cur.rowcount


# Keep backwards compatibility for existing US-specific code
def insert_feed_us_pg(conn, feed):
    r"""Legacy function for backward compatibility. Use insert_feed_pg instead."""
    return insert_feed_pg(conn, feed, region="us")


def insert_feed_if_not_exists_pg(conn, feed, region="us"):
    r"""Inserts a feed record only if it doesn't already exist in PostgreSQL.

    Args:
        conn: PostgreSQL database connection
        feed: Tuple containing (id, url, timestamp, title, inserted_at)
        region: The region code (us, sg, eu) to determine which feeds table to use

    Returns:
        tuple: (was_inserted: bool, row_id: int or None)
               was_inserted is True if new record was inserted
               row_id is the ID of the inserted record, or None if already existed
    """
    # Extract url and title from the feed tuple
    _, url, _, title, _ = feed

    # Check if feed already exists
    if feed_exists_pg(conn, url, title, region):
        return (False, None)

    # If not exists, insert it
    row_count = insert_feed_pg(conn, feed, region)
    return (True, row_count)
