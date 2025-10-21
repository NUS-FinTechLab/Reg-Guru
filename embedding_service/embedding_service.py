"""Embedding and query service for Reg-Guru."""

import os
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

import chromadb
from chromadb.api import configuration as chroma_configuration
import torch
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv(override=True)

_DEFAULT_CHROMADB_HOST = "ec2-13-228-79-108.ap-southeast-1.compute.amazonaws.com"
_DEFAULT_CHROMADB_PORT = 80
_DEFAULT_CHROMADB_COLLECTION = os.getenv(
    "CHROMADB_COLLECTION", "reg_guru_embeddings"
).strip()

# Load model once at startup
# Setting use_fp16 to True speeds up computation with a slight performance degradation
if torch.cuda.is_available():
    device = "cuda:0"
    use_fp16 = True
else:
    device = "cpu"
    use_fp16 = False

model_name = os.getenv("EMBEDDER_MODEL", "BAAI/bge-m3")
device = "cuda" if torch.cuda.is_available() else "cpu"
model = SentenceTransformer(model_name, device=device)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
executor = ThreadPoolExecutor(max_workers=1)

_COLLECTION: Optional[chromadb.Collection] = None
_CHROMADB_CLIENT: Optional[chromadb.HttpClient] = None


def _ensure_legacy_chroma_support() -> None:
    """Patch Chroma loader to handle legacy metadata."""
    if getattr(_ensure_legacy_chroma_support, "_patched", False):
        return

    from_json = chroma_configuration.CollectionConfigurationInternal.from_json
    if hasattr(from_json, "__func__"):
        original = from_json.__func__

        def patched(cls, json_map):
            if json_map is not None:
                json_map = dict(json_map)
                json_map.setdefault("_type", "CollectionConfigurationInternal")
                json_map.pop("vector_index", None)
                json_map.pop("embedding_function", None)
            return original(cls, json_map)

        chroma_configuration.CollectionConfigurationInternal.from_json = classmethod(patched)  # type: ignore[assignment]
        _ensure_legacy_chroma_support._patched = True


_ensure_legacy_chroma_support()


def _build_chromadb_client() -> chromadb.Client:
    global _CHROMADB_CLIENT

    if _CHROMADB_CLIENT is None:
        host = os.getenv("CHROMADB_HOST", _DEFAULT_CHROMADB_HOST).strip()
        port_value = os.getenv("CHROMADB_PORT", str(_DEFAULT_CHROMADB_PORT)).strip()
        token = os.getenv("CHROMADB_AUTH_TOKEN", "").strip()

        try:
            port = int(port_value)
        except ValueError as exc:
            raise RuntimeError(
                f"Invalid CHROMADB_PORT value '{port_value}'. Please provide an integer port."
            ) from exc

        headers = None
        if token:
            headers = {"Authorization": f"Bearer {token}"}

        _CHROMADB_CLIENT = chromadb.HttpClient(host=host, port=port, headers=headers)

    return _CHROMADB_CLIENT


def _get_collection() -> chromadb.Collection:
    global _COLLECTION

    if _COLLECTION is None:
        client = _build_chromadb_client()
        _COLLECTION = client.get_or_create_collection(
            name=_DEFAULT_CHROMADB_COLLECTION,
            embedding_function=None,
        )

    return _COLLECTION


def _embedding_tag(region: str) -> str:
    return f"{region}_embeddings"


class EmbedRequest(BaseModel):
    texts: List[str]
    batch_size: int = 16


class EmbedResponse(BaseModel):
    embeddings: List[List[float]]


class QueryRequest(BaseModel):
    query_texts: List[str]
    region: str
    n_results: int = 5


class QueryResponse(BaseModel):
    documents: List[List[str]]
    metadatas: List[List[Dict[str, Any]]]
    distances: List[List[float]]


@app.post("/embed", response_model=EmbedResponse)
def embed(request: EmbedRequest):
    def run():
        # all_embeddings = []
        # for i in range(0, len(request.texts), request.batch_size):
        #     batch_texts = request.texts[i : i + request.batch_size]
        #     batch_embeddings = model.encode(
        #         batch_texts, batch_size=len(batch_texts)
        #     )
        #     if hasattr(batch_embeddings, "tolist"):
        #         batch_embeddings = batch_embeddings.tolist()
        #     all_embeddings.extend(batch_embeddings)
        # return all_embeddings
        embeddings = model.encode(request.texts, batch_size=request.batch_size)
        if hasattr(embeddings, "tolist"):
            embeddings = embeddings.tolist()
        return embeddings

    return {"embeddings": executor.submit(run).result()}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    def run():
        texts = [text for text in request.query_texts if text and text.strip()]
        if not texts:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        query_embeddings = model.encode(texts, batch_size=min(len(texts), 12))
        if hasattr(query_embeddings, "tolist"):
            query_embeddings = query_embeddings.tolist()
        if not query_embeddings:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        collection = _get_collection()
        embedding_tag = _embedding_tag(request.region)
        results = collection.query(
            query_embeddings=query_embeddings,
            n_results=request.n_results,
            include=["documents", "metadatas", "distances"],
            where={"embedding_name": embedding_tag},
        )

        return {
            "documents": results.get("documents", [[]]),
            "metadatas": results.get("metadatas", [[]]),
            "distances": results.get("distances", [[]]),
        }

    return executor.submit(run).result()
