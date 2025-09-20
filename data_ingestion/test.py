import os
import sys
from unittest import result

# Add the parent directories to the Python path to resolve imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, src_dir)

from src.common.embedding_helper import get_testing_chromadb_client

if __name__ == "__main__":
    chromadb_client = get_testing_chromadb_client('sg', 'chromadb_sg')
    col = chromadb_client.get_or_create_collection(name="sg_embeddings")

    title = "Financial Services and Markets Act 2022"
    results = col.get(
        where={"title": {"$eq": title}},     # or just {"title": title} depending on your Chroma version
        include=["metadatas", "embeddings", "documents"]  # pick what you need
    )

    # results["embeddings"] is a list aligned with results["ids"]
    print(results)
