import os
import re
import boto3
import hashlib
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
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY")
        )
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.feed_obj = "data_ingestion/raw/eu/eurlex-feed"
        # self.chroma_directory = "s3://regguru/data_ingestion/chroma/eu"
        self.chroma_directory = "backend/data_ingestion/chroma/eu"
        self.temp_collection_name = "eu-feed"
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
    
    def extract_meta(self, log_id): # Should process metadata in advance and store in Silver?
        """Return ready-to-use metadata"""
        query = f"SELECT * FROM bronze.feeds_test_eu WHERE log_id = {log_id} LIMIT 2" # test
        new_entries = db_execute(query)
        meta = pd.DataFrame(new_entries, columns=new_entries[0].keys() if new_entries else [])
        meta['celex'] = meta["title"].apply(lambda t: t.split(':')[1])
        return meta
    
    def make_id(key):
        # key is an s3 key
        # data_ingestion/raw/...
        # normalise key: Remove data_ingestion/raw/
        norm_key = '/'.join(key.split('/')[2:])
        return hashlib.md5(norm_key.encode("utf-8")).hexdigest()[:16]

    def process_documents(self, log_id):
        new_meta = self.extract_meta(log_id)
        ch_client = PersistentClient(path="./chroma_data")
        collection = ch_client.get_or_create_collection(self.temp_collection_name)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Slightly larger chunks
            chunk_overlap=200
        )
        model = SentenceTransformer("BAAI/bge-m3")
        paginator = self.s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=self.feed_obj+'/'+str(log_id)):
            for obj in page.get("Contents", []):
                celex = obj.split('/')[-1].split('.')[0]
                if celex != "metadata":
                    text = self.extract_text(obj)
                    meta = new_meta[new_meta['celex'] == celex].to_dict()
                    chunks = text_splitter.split(text)
                    texts = [chunk for chunk in chunks]
                    embeddings = model.encode(texts)
                    collection.add(
                        documents=texts,
                        metadatas=[meta for _ in range(len(texts))],
                        embedding=embeddings.embed_documents(texts),
                        ids=[f"{self.make_id(obj)}_{i}" for i in range(len(texts))]
                    )
                    # ch_client.persist()
        return