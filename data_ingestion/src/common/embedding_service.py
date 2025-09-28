"""Embedding service using FastAPI and SentenceTransformer."""
"""cd data_ingestion/src"""
"""uvicorn eu.EUEmbedderService:app --host 0.0.0.0 --port 6000 --reload"""

import os
import chromadb
import torch
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from concurrent.futures import ThreadPoolExecutor
from sentence_transformers import SentenceTransformer

# Load model once at startup
# Setting use_fp16 to True speeds up computation with a slight performance degradation
device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
model_name = os.getenv("EMBEDDER_MODEL", "BAAI/bge-m3")
model = SentenceTransformer(model_name, use_fp16= device != 'cpu', devices=[device])
app = FastAPI()
executor = ThreadPoolExecutor(max_workers=1)

class EmbedRequest(BaseModel):
    texts: List[str]
    batch_size: int = 16

class EmbedResponse(BaseModel):
    embeddings: List[List[float]]

@app.post("/embed", response_model=EmbedResponse)
def embed(request: EmbedRequest):
    def run():
        all_embeddings = []
        for i in range(0, len(request.texts), request.batch_size):
            batch_texts = request.texts[i:i + request.batch_size]
            batch_embeddings = model.encode(batch_texts, batch_size=min(len(batch_texts), 12))
            all_embeddings.extend(batch_embeddings.tolist())
        return all_embeddings

    return {"embeddings": executor.submit(run).result()}