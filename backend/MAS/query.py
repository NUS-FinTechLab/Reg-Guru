import chromadb

chroma_client = chromadb.PersistentClient(path='./')
collection = chroma_client.get_or_create_collection(name="embeddings")

query = "What is the definition of a Security?"

results = collection.query(
    query_texts=[query],
    n_results=2
)

print(results)