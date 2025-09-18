import pdfplumber
import mimetypes
import subprocess
from bs4 import BeautifulSoup
import os
import sys
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directories to the Python path to resolve imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, src_dir)

from common.helper import insert_feed_if_not_exists_pg

def process_sso_data(raw_data):
    """
    Process SSO file paths and return a list of dictionaries with structured information.
    Note: Duplicate filtering is now handled in the scraper phase to avoid unnecessary downloads.
    
    Args:
        raw_data: Dictionary containing downloaded files and their information
        db_path: Deprecated parameter (kept for compatibility)
        
    Returns:
        list: List of processed data dictionaries, one for each file
    """
    file_paths = raw_data.get('downloaded_files', [])
    files_information = raw_data.get('files_information', [])
    processed_docs = []
    
    # Set up database connection for recording processed documents
    conn = None
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            dbname=os.getenv("DB_NAME")
        )
        print(f"Connected to PostgreSQL database for recording processed documents")
    except Exception as e:
        print(f"Warning: Could not connect to database: {str(e)}")
    processed_count = 0

    for file_path, file_info in zip(file_paths, files_information):
        if not os.path.exists(file_path):
            continue
            
        # Extract metadata
        url = file_info.get('url', 'N/A')
        title = file_info.get('title', 'N/A')
            
        chunks = []
        metadata = {
            "title": title,
            "link": url
        }

        try:
            # Check actual file type using the 'file' command
            result = subprocess.run(['file', '--mime-type', file_path], 
                                  capture_output=True, text=True)
            mime_type = result.stdout.split(':')[1].strip()
            
            if 'pdf' in mime_type:
                # Process as PDF
                chunks = process_pdf_file(file_path)
            elif 'html' in mime_type or 'text' in mime_type:
                # Process as HTML/text file
                chunks = process_html_file(file_path)
            else:
                continue
                
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
            continue

        doc = {
            "content": "\n".join(chunks),
            "metadata": metadata,
            "type": "sso_act",  # Changed to reflect SSO document type
        }
        
        print(doc)
        
        processed_docs.append(doc)
        processed_count += 1
        
        # Record that we've processed this document (if database connection available)
        if conn:
            try:
                # Create feed record: (id, url, timestamp, title, inserted_at)
                current_time = datetime.now().isoformat()
                # Generate a simple ID based on URL hash for consistency
                doc_id = abs(hash(url)) % (10**8)  # Simple ID generation
                feed_data = (doc_id, url, None, title, current_time)  # timestamp is None for SSO
                
                was_inserted, row_id = insert_feed_if_not_exists_pg(conn, feed_data, "sg")
                if was_inserted:
                    print(f"Recorded document in database: {title}")
                
            except Exception as e:
                print(f"Warning: Could not record document in database: {str(e)}")
    
    # Close database connection
    if conn:
        conn.close()
    
    # Print processing summary
    total_docs = len(file_paths)
    print(f"\n=== Processing Summary ===")
    print(f"Total documents to process: {total_docs}")
    print(f"Documents successfully processed: {processed_count}")
    print(f"Documents failed to process: {total_docs - processed_count}")
    
    return processed_docs

def process_pdf_file(file_path):
    """Process a PDF file and extract text content."""
    chunks = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for _, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    chunks.append(text)

            print(f"CHUNK: {chunks}")
    except Exception as e:
        print(f"Error processing PDF {file_path}: {str(e)}")
    return chunks

def process_html_file(file_path):
    """Process an HTML file and extract text content."""
    chunks = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
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
        print(f"Error processing HTML {file_path}: {str(e)}")
    return chunks