from ...common.embedding_helper import (
    embed_batch,
    get_testing_chromadb_client,
    get_text_splitter,
)

# FinCEN-specific configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def embed_into_chromadb(docs, collection_name="us_embeddings"):
    """Embed FinCEN documents into Chroma vector database."""
    chroma_client = get_testing_chromadb_client('us', 'chromadb_us')
    collection = chroma_client.get_or_create_collection(name=collection_name)
    
    # Split documents into chunks for better embedding
    text_splitter = get_text_splitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    all_chunks = []
    all_metadata = []
    chunk_ids = []
    
    for i, doc in enumerate(docs):
        content = doc.get('content', '')
        if not content.strip():
            continue
            
        # Split content into chunks for better embedding
        chunks = text_splitter.split_text(content)
        
        for j, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            
            all_chunks.append(chunk)
            all_metadata.append(doc.get('metadata', {}))
            chunk_ids.append((i, j))  # Store document and chunk indices

    if not all_chunks:
        return collection
    
    # Batch embed all chunks for efficiency
    embeddings = embed_batch(all_chunks, batch_size=16)
    
    # Store in ChromaDB in batches
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        end_idx = min(i + batch_size, len(all_chunks))
        
        collection.add(
            documents=all_chunks[i:end_idx],
            metadatas=all_metadata[i:end_idx],
            embeddings=embeddings[i:end_idx],
            ids=[f"doc{doc_idx}_chunk{chunk_idx}" for doc_idx, chunk_idx in chunk_ids[i:end_idx]],
        )
        
    return collection
