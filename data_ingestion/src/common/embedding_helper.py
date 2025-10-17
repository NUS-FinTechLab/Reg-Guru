import os

from FlagEmbedding import BGEM3FlagModel
import chromadb


_DEFAULT_CHROMADB_HOST = "ec2-13-228-79-108.ap-southeast-1.compute.amazonaws.com"
_DEFAULT_CHROMADB_PORT = 80

model = BGEM3FlagModel(
    "BAAI/bge-m3", use_fp16=True, devices=["cuda:0"]
)  # Setting use_fp16 to True speeds up computation with a slight performance degradation


def get_chromadb_client(region, collection_name):
    """Return an HttpClient for the shared ChromaDB deployment."""

    host = os.getenv("CHROMADB_HOST", _DEFAULT_CHROMADB_HOST).strip()
    port_value = os.getenv("CHROMADB_PORT", str(_DEFAULT_CHROMADB_PORT)).strip()

    try:
        port = int(port_value)
    except ValueError as exc:
        raise ValueError(
            f"Invalid CHROMADB_PORT value '{port_value}'. Please provide an integer port."
        ) from exc

    return chromadb.HttpClient(host=host, port=port)


def get_text_splitter(chunk_size=1000, chunk_overlap=200):
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )
    return text_splitter


def embed_texts(texts):
    embeddings = model.encode(texts, batch_size=12)["dense_vecs"]
    return embeddings


def embed_batch(texts, batch_size=16):
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        batch_embeddings = model.encode(batch_texts, batch_size=12)["dense_vecs"]
        all_embeddings.extend(batch_embeddings)
    return all_embeddings


def query_with_date_range(collection, query_text, start_date, end_date, n_results=5):
    query_embedding = embed_texts(query_text)
    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())

    results = collection.query(
        query_embeddings=[query_embedding],
        where={
            "$and": [
                {"timestamp": {"$gte": start_timestamp}},
                {"timestamp": {"$lte": end_timestamp}},
            ]
        },
        n_results=n_results,
    )
    return results
