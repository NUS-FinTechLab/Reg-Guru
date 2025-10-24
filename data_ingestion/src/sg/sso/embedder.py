from typing import Iterable, List, Tuple

from ...common.embedding_helper import (
    embed_batch,
    get_default_collection,
    get_text_splitter,
)


CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def _split_documents(docs: Iterable[dict]) -> Tuple[List[str], List[dict], List[str]]:
    """Chunk documents and prepare metadata for embedding."""
    splitter = get_text_splitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    chunks: List[str] = []
    metadatas: List[dict] = []
    chunk_ids: List[str] = []

    for doc_index, doc in enumerate(docs):
        content = doc.get("content", "").strip()
        if not content:
            continue

        # Break the long document into overlapping chunks for better retrieval.
        for chunk_index, chunk in enumerate(splitter.split_text(content)):
            chunk_text = chunk.strip()
            if not chunk_text:
                continue
            chunks.append(chunk_text)
            metadatas.append(doc.get("metadata", {}))
            chunk_ids.append(f"doc{doc_index}_chunk{chunk_index}")

    return chunks, metadatas, chunk_ids


def embed_into_chromadb(docs: Iterable[dict], embedding_name: str = "sg_embeddings"):
    """Embed processed documents into a persistent Chroma collection."""
    collection = get_default_collection()

    chunks, metadatas, chunk_ids = _split_documents(docs)
    if not chunks:
        print("No content to embed for this batch.")
        return collection

    # Encode the text chunks in moderately-sized batches to amortize model calls.
    embeddings = embed_batch(chunks, batch_size=16)

    enriched_metadatas: List[dict] = []
    for metadata in metadatas:
        metadata_copy = dict(metadata or {})
        metadata_copy["embedding_name"] = embedding_name
        enriched_metadatas.append(metadata_copy)

    batch_size = 100
    for start in range(0, len(chunks), batch_size):
        end = start + batch_size
        collection.upsert(
            documents=chunks[start:end],
            metadatas=enriched_metadatas[start:end],
            embeddings=embeddings[start:end],
            ids=[f"{embedding_name}:{chunk_id}" for chunk_id in chunk_ids[start:end]],
        )

    print(f"Embedded {len(chunks)} chunks under tag '{embedding_name}'.")
    return collection
