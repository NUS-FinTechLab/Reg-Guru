def get_chroma_collection(region):
    from data_ingestion.src.common.embedding_helper import get_testing_chromadb_client
    chroma_client = get_testing_chromadb_client(region, f"chromadb_{region}")
    collection = chroma_client.get_or_create_collection(name=region+"_embeddings")
    return collection