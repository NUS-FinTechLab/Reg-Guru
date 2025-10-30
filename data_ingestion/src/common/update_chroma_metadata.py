from embedding_helper import get_chromadb_client, get_default_collection
from chromadb import Settings
import chromadb

client = get_chromadb_client()
client.reset()  # reset the database so we can run this script multiple times
col = client.get_or_create_collection("test")
count = col.count()


def update_metadata(metadata: dict):
    return {k: v.strip() for k, v in metadata.items()}


for i in range(0, count, 10):
    batch = col.get(include=["metadatas"], limit=10, offset=i)
    col.update(ids=batch["ids"], metadatas=[update_metadata(metadata) for metadata in batch["metadatas"]])