from FlagEmbedding import BGEM3FlagModel
import chromadb

model = BGEM3FlagModel('BAAI/bge-m3',  
                       use_fp16=True,
                       devices=['cuda:0']) # Setting use_fp16 to True speeds up computation with a slight performance degradation

def get_testing_chromadb_client():
    chroma_client = chromadb.PersistentClient(path="../us/fincen/chromadb_fincen")
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


