from typing import Iterable, List, Tuple

from ...common.embedding_helper import embed_batch, get_testing_chromadb_client, get_text_splitter


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


def embed_into_chromadb(docs: Iterable[dict], collection_name: str = "sg_embeddings"):
    """Embed processed documents into a persistent Chroma collection."""
    chroma_client = get_testing_chromadb_client("sg", "chromadb_sg")
    collection = chroma_client.get_or_create_collection(name=collection_name)

    chunks, metadatas, chunk_ids = _split_documents(docs)
    if not chunks:
        print("No content to embed for this batch.")
        return collection

    # Encode the text chunks in moderately-sized batches to amortize model calls.
    embeddings = embed_batch(chunks, batch_size=16)

    batch_size = 100
    for start in range(0, len(chunks), batch_size):
        end = start + batch_size
        collection.add(
            documents=chunks[start:end],
            metadatas=metadatas[start:end],
            embeddings=embeddings[start:end],
            ids=chunk_ids[start:end],
        )

    print(f"Embedded {len(chunks)} chunks into collection '{collection_name}'.")
    return collection
