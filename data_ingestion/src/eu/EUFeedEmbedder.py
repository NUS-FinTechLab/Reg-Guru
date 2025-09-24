import os
import re
import boto3
import pandas as pd
from common.database import db_execute
from bs4 import BeautifulSoup
from chromadb import PersistentClient
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import BSHTMLLoader, UnstructuredXMLLoader
from langchain_huggingface import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
load_dotenv(override=True)

class EUFeedEmbedder:
    def __init__(self, collection_name):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY")
        )
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.feed_obj = "data_ingestion/raw/eu/eurlex-feed"
        # self.chroma_directory = "s3://regguru/data_ingestion/chroma/eu"
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.chroma_directory = os.path.join(current_dir, '..', '..', 'chroma', 'eu', 'chromadb_eu')
        self.collection_name = collection_name
        return
    
    def extract_text(self, key):
        obj = self.s3.get_object(Bucket=self.bucket_name, Key=key)
        xml_content = obj['Body'].read()
        soup = BeautifulSoup(xml_content, "lxml")
        # Find the main content of regulation
        document = soup.find("div", id="PP4Contents")
        # Remove script and style
        for tag in document(["script", "style"]):
            tag.decompose()
        # Extract texts in p
        paragraphs = []
        for p in document.find_all("p"):
            text = p.get_text(" ", strip=True)
            if text:
                text = text.replace("\xa0", " ")
                text = re.sub(r"[ \t]+", " ", text)
                text = re.sub(r"\n+", "\n", text)
                text = text.strip()
                paragraphs.append(text)
        plain_text = '\n'.join(paragraphs)
        return plain_text
    
    def extract_meta(self, log_id):
        query = f"SELECT title, link, published, author, celex_number FROM silver.metadata WHERE log_id = {log_id}"
        meta = db_execute(query)
        meta_df = pd.DataFrame([dict(row) for row in meta])
        meta_df['published'] = pd.to_datetime(meta_df['published'], errors='raise').apply(lambda x: int(x.timestamp()) if pd.notnull(x) else None)
        return meta_df

    def process_documents(self, log_id):
        new_meta = self.extract_meta(log_id)
        ch_client = PersistentClient(path=self.chroma_directory)
        collection = ch_client.get_or_create_collection(self.collection_name)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Slightly larger chunks
            chunk_overlap=200
        )
        model = SentenceTransformer("all-MiniLM-L6-v2")
        print("model loaded")
        response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=self.feed_obj+'/'+str(log_id))
        if "Contents" in response:
            for obj in response["Contents"]:
                key = obj['Key']
                celex = key.split('/')[-1].split('.')[0]
                if celex in new_meta['celex_number'].values: #Test
                    print(f"Processing {key} ...")
                    text = self.extract_text(key)
                    meta = new_meta[new_meta['celex_number'] == celex].to_dict(orient='records')[0] # Ensure single record
                    print(meta)
                    chunks = text_splitter.split_text(text)
                    texts = [chunk for chunk in chunks]
                    collection.add(
                        documents=texts,
                        metadatas=[meta for _ in range(len(texts))],
                        embeddings=model.encode(texts),
                        ids=[f"{'/'.join(key.split('/')[2:])}_{i}" for i in range(len(texts))]
                    ) # an s3 key: data_ingestion/raw/... # normalise key: Remove data_ingestion/raw/
                    break
                else:
                    print(f"CELEX {celex} not in metadata, skipping {key}.")
            print("Embedding finished")
        else:
            print("No objects found for the given log_id.")           
        
        return
    
    def test_collection(self):
        ch_client = PersistentClient(path=self.chroma_directory)
        collection = ch_client.get_or_create_collection(self.collection_name)
        assert collection.count() > 0, f"Collection {self.collection_name} is empty!"
        results = collection.query(
            query_texts=[
                "How to combat VAT fraud?"],
            n_results=3
        )
        print(results)
        return

# if __name__ == '__main__':
#     embedder = EUFeedEmbedder("eu_test")
#     embedder.process_documents(18)
#     embedder.test_collection()