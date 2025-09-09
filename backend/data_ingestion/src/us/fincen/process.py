import os

def process_fincen_data(file_paths):
    """
    Process FinCEN PDF file paths and return a list of dictionaries with structured information.
    
    Args:
        file_paths: List of file paths to downloaded PDF files
        
    Returns:
        list: List of processed data dictionaries, one for each PDF file
    """
    processed_docs = []
    
    for file_path in file_paths:
        # Extract filename for better identification
        filename = os.path.basename(file_path)
        
        doc = {
            "content": file_path,  # Store the file path as content for now
            "source": "fincen",
            "type": "pdf",
            "filename": filename,
            "file_path": file_path
        }
        processed_docs.append(doc)
    
    return processed_docs
