import pdfplumber
import os
import chromadb

chroma_client = chromadb.PersistentClient(path="./")
collection = chroma_client.get_or_create_collection(name="embeddings")

def insert_into_chromadb(file_name, chunks, metadata):
    collection.add(
        documents=chunks,
        metadatas=metadata,
        ids=[f"{file_name}_page_{i + 1}" for i in range(len(chunks))],
    )

pdf_dir = "downloads"

# Loop through all PDF files in the directory
for pdf_file in os.listdir(pdf_dir):
    pdf_path = os.path.join(pdf_dir, pdf_file)

    print(f"Processing {pdf_path}")

    if pdf_file.endswith(".pdf"):
        chunks = []
        metadata = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    chunks.append(text)
                    metadata.append({"page": f"Page {page_number}"})

        insert_into_chromadb(pdf_file, chunks, metadata)

    print(f"Finished processing {pdf_path}")