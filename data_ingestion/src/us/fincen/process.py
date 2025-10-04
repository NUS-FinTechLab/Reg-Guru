import io
import os
from datetime import datetime

import boto3
import pdfplumber
import psycopg2
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

from ...common.helper import feed_exists_pg, insert_feed_if_not_exists_pg

def process_fincen_data(raw_data, db_path=None):
    """
    Process FinCEN documents that were stored in S3 or on disk during ingestion.

    Args:
        raw_data: Dictionary containing document metadata and storage info.
        db_path: Deprecated parameter kept for compatibility.

    Returns:
        list: List of processed data dictionaries, one for each advisory document.
    """

    documents_info = raw_data.get("documents", [])
    processed_docs = []

    s3_client = None
    processed_count = 0

    # Optional database connection for feed bookkeeping
    conn = None
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            dbname=os.getenv("DB_NAME"),
        )
        print("Connected to PostgreSQL database for recording processed documents")
    except Exception as e:
        print(f"Warning: Could not connect to database: {str(e)}")

    for info in documents_info:
        storage = info.get("storage", {})
        url = info.get("url", "N/A")
        title = info.get("title", "N/A")
        timestamp = info.get("timestamp", "N/A")
        doc_id = info.get("doc_id")

        file_bytes = None

        already_recorded = False
        if conn:
            try:
                already_recorded = feed_exists_pg(conn, url, title or "N/A", region="us")
            except Exception as db_err:
                print(
                    f"Warning: Could not verify existing FinCEN feed for {url}: {str(db_err)}"
                )

        if already_recorded:
            print(f"Skipping already processed document found in database: {title}")
            continue

        storage_type = storage.get("type")
        try:
            if storage_type == "s3":
                if not s3_client:
                    s3_client = boto3.client(
                        "s3",
                        aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
                        aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY"),
                        region_name=os.getenv("AWS_REGION"),
                    )
                obj = s3_client.get_object(Bucket=storage["bucket"], Key=storage["key"])
                file_bytes = obj["Body"].read()
            elif storage_type == "local":
                local_path = storage.get("path")
                if not local_path or not os.path.exists(local_path):
                    print(f"Missing local file for {url}; skipping")
                    continue
                with open(local_path, "rb") as fh:
                    file_bytes = fh.read()
            else:
                print(f"Unknown storage type for {url}; skipping")
                continue
        except Exception as e:
            print(f"Error retrieving document for {url}: {str(e)}")
            continue

        if not file_bytes:
            continue

        chunks = process_pdf_file(file_bytes)
        if not chunks:
            continue

        metadata = {
            "timestamp": timestamp,
            "title": title,
            "link": url,
            "doc_id": doc_id,
        }

        doc = {
            "content": "\n".join(chunks),
            "metadata": metadata,
            "type": "fincen_advisory",
        }

        processed_docs.append(doc)
        processed_count += 1

        if conn:
            try:
                current_time = datetime.now().isoformat()
                record_id = abs(hash(url)) % (10**8)
                feed_data = (record_id, url, timestamp, title, current_time)
                was_inserted, _ = insert_feed_if_not_exists_pg(conn, feed_data)
                if was_inserted:
                    print(f"Recorded document in database: {title}")
            except Exception as e:
                print(f"Warning: Could not record document in database: {str(e)}")

    if conn:
        conn.close()

    total_docs = len(documents_info)
    print("\n=== Processing Summary ===")
    print(f"Total documents to process: {total_docs}")
    print(f"Documents successfully processed: {processed_count}")
    print(f"Documents failed to process: {total_docs - processed_count}")

    return processed_docs

def process_pdf_file(source):
    """Process PDF content (bytes or path) and extract text."""
    chunks = []
    try:
        if isinstance(source, bytes):
            pdf_stream = io.BytesIO(source)
            context = pdfplumber.open(pdf_stream)
        else:
            context = pdfplumber.open(source)

        with context as pdf:
            for _, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    chunks.append(text)
    except Exception as e:
        print(f"Error processing PDF {source}: {str(e)}")
    return chunks

def process_html_file(source):
    """Process an HTML file and extract text content."""
    chunks = []
    try:
        if isinstance(source, bytes):
            content = source.decode('utf-8', errors='ignore')
        else:
            with open(source, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()

        soup = BeautifulSoup(content, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        # Extract text
        text = soup.get_text()
        if text.strip():
            chunks.append(text.strip())
    except Exception as e:
        print(f"Error processing HTML {source}: {str(e)}")
    return chunks
