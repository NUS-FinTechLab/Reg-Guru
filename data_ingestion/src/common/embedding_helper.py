from tracemalloc import start
from FlagEmbedding import BGEM3FlagModel
import chromadb

model = BGEM3FlagModel('BAAI/bge-m3',  
                       use_fp16=True,
                       devices=['cuda:0']) # Setting use_fp16 to True speeds up computation with a slight performance degradation

def get_testing_chromadb_client(region, collection_name):
    import os
    # Get the absolute path to the chromadb_fincen directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    chroma_path = os.path.join(current_dir, '..', '..', 'chroma', region, collection_name)
    chroma_client = chromadb.PersistentClient(path=chroma_path)
    return chroma_client

def get_text_splitter(chunk_size=1000, chunk_overlap=200):
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    return text_splitter

def embed_texts(texts):
    embeddings = model.encode(texts, batch_size=12)['dense_vecs']
    return embeddings

def embed_batch(texts, batch_size=16):
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_embeddings = model.encode(batch_texts, batch_size=12)['dense_vecs']
        all_embeddings.extend(batch_embeddings)
    return all_embeddings

def query_with_date_range(collection, query_text, start_date, end_date, n_results=5):
    query_embedding = embed_texts(query_text)
    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())

    results = collection.query(
        query_embeddings=[query_embedding],
        where={
            '$and': [
                {'timestamp': {'$gte': start_timestamp}},
                {'timestamp': {'$lte': end_timestamp}}
            ]
        },
        n_results=n_results
    )
    return results

