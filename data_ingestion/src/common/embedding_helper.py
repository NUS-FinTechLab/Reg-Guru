""" Helper functions for sending requests to embedding service and managing ChromaDB collections."""

from gc import collect
import os
import requests
import chromadb
from typing import Dict, Optional
from dotenv import load_dotenv
load_dotenv(override=True)

_DEFAULT_CHROMADB_HOST = "ec2-13-228-79-108.ap-southeast-1.compute.amazonaws.com"
_DEFAULT_CHROMADB_PORT = 80
_DEFAULT_CHROMADB_COLLECTION = os.getenv("CHROMADB_COLLECTION", "reg_guru_embeddings").strip()
_CHROMADB_CLIENT: Optional[chromadb.HttpClient] = None
_CHROMADB_COLLECTION_HANDLE: Optional[chromadb.Collection] = None
_EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:6000").strip()
_EMBED_BATCH_SIZE = 16
_DEFAULT_CHUNK_SIZE = 1000
_DEFAULT_CHUNK_OVERLAP = 200
# ChromaDB utils
def get_chromadb_client(*_, **__) -> chromadb.HttpClient:
    """Return a cached HttpClient for the shared ChromaDB deployment."""

    global _CHROMADB_CLIENT

    if _CHROMADB_CLIENT is None:
        host = os.getenv("CHROMADB_HOST", _DEFAULT_CHROMADB_HOST).strip()
        port_value = os.getenv("CHROMADB_PORT", str(_DEFAULT_CHROMADB_PORT)).strip()
        token = os.getenv("CHROMADB_AUTH_TOKEN", "").strip()

        try:
            port = int(port_value)
        except ValueError as exc:
            raise ValueError(
                f"Invalid CHROMADB_PORT value '{port_value}'. Please provide an integer port."
            ) from exc

        headers: Optional[Dict[str, str]] = None
        if token:
            headers = {"Authorization": f"Bearer {token}"}

        _CHROMADB_CLIENT = chromadb.HttpClient(host=host, port=port, headers=headers)

    return _CHROMADB_CLIENT


def get_default_collection() -> chromadb.Collection:
    """Return the shared ChromaDB collection used across all regions."""

    global _CHROMADB_COLLECTION_HANDLE

    if _CHROMADB_COLLECTION_HANDLE is None:
        client = get_chromadb_client()
        _CHROMADB_COLLECTION_HANDLE = client.get_or_create_collection(
            name=_DEFAULT_CHROMADB_COLLECTION,
            embedding_function=None,
        )

    return _CHROMADB_COLLECTION_HANDLE

def get_collection(collection_name) -> chromadb.Collection:
    client = get_chromadb_client()
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=None,
    )
    return collection


def get_default_collection_name() -> str:
    return _DEFAULT_CHROMADB_COLLECTION

def delete_collection(collection_name):
    client = get_chromadb_client()
    try:
        client.delete_collection(name=collection_name)
        print(f"Collection {collection_name} deleted.")
    except Exception as e:
        print(e)
    return

def query_texts(texts, n_results=5, collection_name=_DEFAULT_CHROMADB_COLLECTION):
    query_embeddings = embed_texts(texts)
    if collection_name == _DEFAULT_CHROMADB_COLLECTION:
        collection = get_default_collection()
    else:
        collection = get_collection(collection_name)
    results = collection.query(
        query_embeddings=query_embeddings,
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    return results

def query_texts_with_filters(texts, filters, n_results=5):
    query_embeddings = embed_texts(texts)
    collection = get_default_collection()
    results = collection.query(
        query_embeddings=query_embeddings,
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
        where=filters
    )
    return results

def query_with_date_range(texts, start_date, end_date, n_results=5):
    """Dates must be yyyy-mm-dd format strings."""
    date_filter = {
            "$and": [
                {"timestamp": {"$gte": start_date}},
                {"timestamp": {"$lte": end_date}},
            ]
        },
    results = query_texts_with_filters(texts, filters=date_filter, n_results=n_results)
    return results

# Embedding utils
def get_text_splitter(chunk_size=_DEFAULT_CHUNK_SIZE, chunk_overlap=_DEFAULT_CHUNK_OVERLAP):
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n",". ", " ", ""],
    )
    return text_splitter


def embed_texts(texts):
    url = f"{_EMBEDDING_SERVICE_URL}/embed"
    all_embeddings = []

    for i in range(0, len(texts), _EMBED_BATCH_SIZE):
        batch_texts = texts[i:i + _EMBED_BATCH_SIZE]
        payload = {"texts": batch_texts, "batch_size": len(batch_texts)}
        try:
            response = requests.post(url, json=payload, timeout=45)
            response.raise_for_status()
            data = response.json()
            all_embeddings.extend(data["embeddings"])
        except (requests.RequestException, ValueError) as exc:
            raise RuntimeError(f"Failed to query embedding service for batch {i}-{i+len(batch_texts)}: {exc}") from exc
        except Exception as e:
            raise Exception(f"Unexpected error during embedding service request: {e}") from e
    return all_embeddings

def embed_and_add_documents(documents, jurisdiction, collection_name=_DEFAULT_CHROMADB_COLLECTION):
        """doc = { 
                    "content": text,
                    "metadata": row.to_dict(),
                    "unique_id" : self.ds_name + "_" + row['unique_id']
                }"""
        if collection_name == _DEFAULT_CHROMADB_COLLECTION:
            collection = get_default_collection()
        else:
            collection = get_collection(collection_name)
        text_splitter = get_text_splitter()
        for doc in documents:
            text = doc["content"]
            metadata = doc["metadata"]
            unique_id = doc["unique_id"]
            metadata.update({"jurisdiction": jurisdiction})
            try:
                chunks = text_splitter.split_text(text)
                texts = [chunk for chunk in chunks]
                embeddings = embed_texts(texts)
                # print(texts)
                collection.upsert(
                    documents=texts,
                    metadatas=[metadata for _ in range(len(texts))],
                    embeddings=embeddings,
                    ids=[f"{unique_id}_{i}" for i in range(len(texts))]
                )
            except Exception as e:
                print(f"Error embedding document {unique_id}:", e)
                raise
        print("Finish batch")
        return collection

if __name__ == "__main__":
    delete_collection("test")
    pass
    # collection = get_default_collection()

    # # 1) Get all ids that start with prefix
    # prefix = "eu_eurlex_test"
    # def batched(iterable, n=1000):
    #     for i in range(0, len(iterable), n):
    #         yield iterable[i:i+n]

    # ids = collection.get(ids=None, include=[]).get("ids", [])
    # to_delete = [i for i in ids if i.startswith(prefix)]
    # print(to_delete)
    # for chunk in batched(to_delete, 1000):
    #     collection.delete(ids=chunk)


