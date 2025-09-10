import pdfplumber

def process_fincen_data(file_paths):
    """
    Process FinCEN PDF file paths and return a list of dictionaries with structured information.
    
    Args:
        file_paths: List of file paths to downloaded PDF files
        
    Returns:
        list: List of processed data dictionaries, one for each PDF file
    """
    print(file_paths)
    processed_docs = []
    
    for file_path in file_paths:
        # Extract filename for better identification
        if file_path.endswith(".pdf"):
            chunks = []
            metadata = []

            with pdfplumber.open(file_path) as pdf:
                for page_number, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    if text:
                        chunks.append(text)
                        metadata.append({"page": f"Page {page_number}"})
        
        doc = {
            "content": "\n".join(chunks),
            "metadata": metadata,
            "type": "fincen_advisory",
        }
        processed_docs.append(doc)
    
    return processed_docs
