from multiprocessing import Pool, current_process
import os
import json
import pandas as pd
import logging
import traceback
from dotenv import load_dotenv
import boto3
from bs4 import BeautifulSoup
import hashlib
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

def extract_mt_code(mt):
    if pd.isna(mt):
        return None
    else:
        return mt[0:5]
    
def extract_mt_term(mt):
    if pd.isna(mt):
        return None
    else:
        return mt[5:]

def decompose_celex(celex):
    sector = celex[0]
    year = celex[1:5]
    return sector, year

def make_id(doc_path):
    return hashlib.md5(doc_path[32:].encode("utf-8")).hexdigest()[:12]

def process_documents_batch(documents, collection):
    pid = current_process().pid
    logging.basicConfig(
        filename=f'log/{pid}.log',          # file to write logs
        level=logging.ERROR,            # log only errors and above
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    AWS_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
    bucket_name = 'regguru'
    # Create an S3 client
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

    la_mtd_file = os.getenv("EU_LEGAL_ACT_METADATA_FILE")
    la_mtd = pd.read_csv(la_mtd_file)
    la_mtd["MT-code"] = la_mtd["MT"].apply(extract_mt_code)
    la_mtd["MT-term"] = la_mtd["MT"].apply(extract_mt_term)
    la_mtd['doc-path'] = "eu/LEG_EN_HTML_20250721_04_08/" + la_mtd['work-id'] + "/" + la_mtd['format'] + "/" + la_mtd['doc']
    la_mtd['mtd-path'] = "eu/LEG_MTD_20250709_22_36/" + la_mtd['work-id'] + "/tree_non_inferred.rdf"

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # Slightly larger chunks
        chunk_overlap=200
    )

    batch_idx = 0

    # for idx, row in documents.iterrows():
    #     try:
    #         # Load document from S3
    #         obj = s3.get_object(Bucket=bucket_name, Key=row["doc-path"])
    #         html_content = obj['Body'].read().decode('utf-8')  # HTML as string
    #         soup = BeautifulSoup(html_content, 'html.parser')
    #         text = soup.get_text(separator="\n")  # plain text
        
    #         # Extract metadata
    #         meta = {}
    #         if soup.title:
    #             meta['title'] = soup.title.string
    #         for m in soup.find_all("meta"):
    #             if m.get("name") and m.get("content"):
    #                 meta[m["name"].lower()] = m["content"]
    #         meta_download = la_mtd[(la_mtd["work-id"] == row["work-id"]) & (la_mtd["doc"] == row["doc"])]
    #         terms = meta_download["TERMS (PT-NPT)"].dropna().astype(str).unique()
    #         meta['eurovoc-terms'] = ';'.join(terms)
    #         mts = meta_download["MT"].dropna().astype(str).unique()
    #         meta['eurovoc-mt'] = ';'.join(mts)

    #         sector, year = decompose_celex(row['celex']) if row['celex'] else (None, None)
    #         meta['celex'] = row['celex'] if row['celex'] else None
    #         meta['celex-sector'] = sector # a character
    #         meta['celex-year'] = int(year) # a 4-digit number

    #         # Split, embed, and store
    #         chunks = text_splitter.split_text(text)
    #         texts = [chunk for chunk in chunks]
    #         embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2", model_kwargs={"device": "cpu"})
    #         collection.add(
    #             documents=texts,
    #             metadatas=[meta for _ in range(len(texts))],
    #             embeddings=embeddings.embed_documents(texts),
    #             ids=[f"{make_id(row['doc-path'])}_{i}" for i in range(len(texts))]
    #         )
    #     except Exception as e:
    #         logging.error("[%d] %d | Error processing %s:\n%s", pid, idx, row["doc-path"], traceback.format_exc())
    #         print(f"[{pid}] {idx} | Error processing {row['doc-path']}")
    #         continue

    #     if (idx + 1) % 100 == 0:
    #         print(f"[{pid}] processed batch {batch_idx}")
    #         batch_idx += 1
    for idx, row in documents.iterrows():
        try:
            # Load document from S3
            obj = s3.get_object(Bucket=bucket_name, Key=row["doc-path"])
            html_content = obj['Body'].read().decode('utf-8')  # HTML as string
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text(separator="\n")  # plain text
        except Exception as e:
            logging.error("[%d] %d | Error fetching %s from S3:\n%s", pid, idx, row["doc-path"], traceback.format_exc())
            print(f"[{pid}] {idx} | Error fetching {row['doc-path']}")
            continue
        
        meta = {}      
        try:
            # Extract metadata  
            if soup.title:
                meta['title'] = soup.title.string
            for m in soup.find_all("meta"):
                if m.get("name") and m.get("content"):
                    meta[m["name"].lower()] = m["content"]
            meta_download = la_mtd[(la_mtd["work-id"] == row["work-id"]) & (la_mtd["doc"] == row["doc"])]
            terms = meta_download["TERMS (PT-NPT)"].dropna().astype(str).unique()
            meta['eurovoc-terms'] = ';'.join(terms)
            mts = meta_download["MT"].dropna().astype(str).unique()
            meta['eurovoc-mt'] = ';'.join(mts)

            sector, year = decompose_celex(row['celex']) if row['celex'] else (None, None)
            meta['celex'] = row['celex'] if row['celex'] else None
            meta['celex-sector'] = sector # a character
            meta['celex-year'] = int(year) # a 4-digit number
        except Exception as e:
            logging.error("[%d] %d | Error extracting metadata for %s:\n%s", pid, idx, row["doc-path"], traceback.format_exc())
            print(f"[{pid}] {idx} | Error extracting metadata for {row['doc-path']}")
            
        
        try:
            # Split, embed, and store
            chunks = text_splitter.split_text(text)
            texts = [chunk for chunk in chunks]
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2", model_kwargs={"device": "cpu"})
            collection.add(
                documents=texts,
                metadatas=[meta for _ in range(len(texts))],
                embeddings=embeddings.embed_documents(texts),
                ids=[f"{make_id(row['doc-path'])}_{i}" for i in range(len(texts))]
            )
        except Exception as e:
            logging.error("[%d] %d | Error processing %s:\n%s", pid, idx, row["doc-path"], traceback.format_exc())
            print(f"[{pid}] {idx} | Error processing {row['doc-path']} | {e}")
            continue

        if (idx + 1) % 100 == 0:
            print(f"[{pid}] processed batch {batch_idx}")
            batch_idx += 1
        
        return True
