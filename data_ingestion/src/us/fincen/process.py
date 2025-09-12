import pdfplumber
import mimetypes
import subprocess
from bs4 import BeautifulSoup
import os

def process_fincen_data(raw_data):
    """
    Process FinCEN file paths and return a list of dictionaries with structured information.
    
    Args:
        raw_data: Dictionary containing downloaded files and their information
        
    Returns:
        list: List of processed data dictionaries, one for each file
    """
    file_paths = raw_data.get('downloaded_files', [])
    files_information = raw_data.get('files_information', [])
    processed_docs = []

    for file_path, file_info in zip(file_paths, files_information):
        if not os.path.exists(file_path):
            print(f"Warning: File {file_path} does not exist, skipping...")
            continue
            
        chunks = []
        metadata = {
            "timestamp": file_info.get('timestamp', 'N/A'),
            "title": file_info.get('title', 'N/A'),
            "link": file_info.get('url', 'N/A')
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
                print(f"Warning: Unsupported file type {mime_type} for {file_path}, skipping...")
                continue
                
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
            continue

        doc = {
            "content": "\n".join(chunks),
            "metadata": metadata,
            "type": "fincen_advisory",
        }
        
        print(doc)
        
        processed_docs.append(doc)
    
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
