from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from typing import List
import os

class DocumentUploader:
    def __init__(self, vectorstore_directory: str = "Database"):
        """
        Initialize DocumentUploader with the directory for the vector store.
        
        Args:
            vectorstore_directory: Directory to store vector databases (default: "Database")
        """
        self.vectorstore_directory = os.path.abspath(vectorstore_directory)
        os.makedirs(self.vectorstore_directory, exist_ok=True)
        self.embeddings = OpenAIEmbeddings()  # Initialize embeddings once

    def _get_loader(self, file_path: str):
        """Determine the appropriate loader based on file extension"""
        file_extension = os.path.splitext(file_path)[1].lower()
        loader_map = {
            '.pdf': PyPDFLoader,
            '.txt': TextLoader,
            '.docx': Docx2txtLoader
        }
        return loader_map.get(file_extension)

    def upload_documents(self, file_paths: List[str]):
        """
        Process and upload multiple documents to the vector store.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            Tuple: (success_count, error_count)
        """
        success_count = 0
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Slightly larger chunks
            chunk_overlap=200,
            length_function=len
        )

        for file_path in file_paths:
            try:
                if not os.path.exists(file_path):
                    print(f"File not found: {file_path}")
                    continue

                Loader = self._get_loader(file_path)
                if not Loader:
                    print(f"Unsupported file type: {file_path}")
                    continue

                # Load and split documents
                documents = Loader(file_path).load()
                chunks = text_splitter.split_documents(documents)

                # Create or update FAISS index
                if os.path.exists(os.path.join(self.vectorstore_directory, "index.faiss")):
                    # Load existing vectorstore and merge new documents
                    vectorstore = FAISS.load_local(
                        folder_path=self.vectorstore_directory,
                        embeddings=self.embeddings,
                        allow_dangerous_deserialization=True
                    )
                    vectorstore.add_documents(chunks)
                else:
                    # Create new vectorstore
                    vectorstore = FAISS.from_documents(chunks, self.embeddings)

                # Save the updated vectorstore
                vectorstore.save_local(folder_path=self.vectorstore_directory)
                success_count += 1
                print(f"Successfully processed: {file_path}")

            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")

        return success_count, len(file_paths) - success_count