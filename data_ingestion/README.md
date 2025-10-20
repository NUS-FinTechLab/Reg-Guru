# Ingestion Pipelines

This directory houses the ingestion stacks that scrape regulatory sources, normalize documents, and embed text chunks into vector stores for Retrieval-Augmented Generation (RAG) workloads. Shared base classes in `src/common/` keep core logic reusable so new jurisdictions can plug into the same scrape → process → embed flow.

Currently implemented pipelines:

- **FinCEN (US)** – Financial Crimes Enforcement Network releases.
- **SSO (Singapore)** – Singapore Statutes Online acts.

---

## Shared Python Environment

All pipelines rely on a dedicated virtual environment (`.venv-bgem3`) because the BGE-M3 embedding model requires NumPy < 2. Use it for both batch ingestion and the long-running embedding/query service.

### Setup

```bash
python -m venv .venv-bgem3
source .venv-bgem3/bin/activate
pip install -r requirements.txt
```

Or activate the existing environment:

```bash
source .venv-bgem3/bin/activate
```

### Key Dependencies

- **FlagEmbedding** – BGE-M3 multilingual embedding model
- **ChromaDB** – Persistent vector store
- **Transformers / Sentence-Transformers** – Text preprocessing utilities
- **PyTorch** – Backing framework for embeddings (with CUDA support if available)

---

## Pipeline Architecture

### Stage 1 – Scrape (`*_Scraper`)

- `BaseScraper` provides throttled HTML requests, pagination helpers, and logging utilities in `src/common/`.
- Dataset scrapers (`FincenScraper`, `SsoScraper`) fetch listing/browse pages via `_request_html`, follow `_next_page_url`, and deduplicate records using `doc_id`.
- Detail pages supply authoritative metadata (titles, published/valid dates, PDF links).
- `log_into_database` ensures the bronze table exists for the dataset and inserts/updates rows under a unique ingestion `log_id`.
- `store_documents` downloads canonical PDFs into `data_ingestion/raw/<region>/<dataset>/<log_id>/` or into S3 when `S3_BUCKET_NAME` is set.

### Stage 2 – Process (`*_Processor`)

- `BaseProcessor` promotes bronze rows into `silver.metadata` once per run through `clean_metadata`.
- `extract_metadata` normalizes timestamp fields (epoch integers) and returns the lookup information needed to locate PDFs.
- `extract_texts` streams one string per PDF page via pdfplumber from either disk or S3.
- `_process_document` applies the shared text cleaner, merges pages, and attaches metadata before yielding batches through `run(batch_size)`.

### Stage 3 – Embed (`embed_into_chromadb`)

- `_split_documents` chunks cleaned text with `CHUNK_SIZE=1000` and `CHUNK_OVERLAP=200`.
- `embed_batch` uses the FlagEmbedding BGE-M3 model in batches of 16 to generate dense vectors.
- `embed_into_chromadb` persists chunk text, embeddings, and metadata into the shared Chroma deployment (`<region>_embeddings`).

### Stage 4 – Orchestrate (`*_Pipeline`)

- Pipelines inherit from `BasePipeline`, exposing `ingest()`, `process(log_id)`, `embed(minibatch)`, and `run()`.
- `ingest()` runs the scraper and returns both `log_id` and the number of inserted/updated rows.
- `process(log_id)` streams normalized document batches from the matching processor.
- `embed(minibatch)` forwards batches to the embedding helper and logs completion.
- `run()` chains the stages, enabling standalone execution or multi-region orchestration via `src/pipelines/run_all.py`.

### Shared Services & Utilities

- `src/common/embedding_service.py` exposes a FastAPI wrapper around embedding and Chroma queries.
- `src/common/embedding_helper.py` provides helpers such as `embed_batch`, `get_chromadb_client`, and collection accessors shared across datasets.
- `src/pipelines/init_database.py` provisions bronze/silver tables for local development.

---

## Dataset Quick Reference

| Dataset | Module | Source | Bronze table | Local storage | Chroma collection | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| FinCEN (US) | `src/us/fincen/` | Advisory listings on fincen.gov | `bronze.feeds_us_fincen` | `data_ingestion/raw/us/fincen/<log_id>/` | `us_embeddings` (remote) | Detail-page crawl captures the first advisory PDF; duplicates skipped by `doc_id`. |
| SSO (Singapore) | `src/sg/sso/` | Singapore Statutes Online browse pages | `bronze.feeds_sg_sso` | `data_ingestion/raw/sg/sso/<log_id>/` | `sg_embeddings` (remote) | Flags superseded/missing statutes and records effective/valid dates from act detail pages. |

---

## Running Pipelines

```bash
source .venv-bgem3/bin/activate

# FinCEN (US)
python3 src/us/fincen/pipeline.py

# Singapore Statutes Online
python3 src/sg/sso/pipeline.py

# Run both sequentially
python3 src/pipelines/run_all.py
```

- Each run prints ingestion counts and the Chroma destination for embedded chunks.
- Provide `S3_BUCKET_NAME` to push PDFs to object storage; otherwise they are written under `data_ingestion/raw/…`.
- Override `CHROMADB_HOST` or `CHROMADB_PORT` to target a different Chroma deployment.

---

## Real-Time Embedding & Query Service

A FastAPI app wraps the embedder and ChromaDB queries so other services do not need to manage the ingestion environment.

```bash
source .venv-bgem3/bin/activate
cd src
uvicorn common.embedding_service:app --host 0.0.0.0 --port 6000 --reload
```

 Environment variables:

- `EMBEDDER_MODEL` – Override the default `BAAI/bge-m3`.
- `CHROMADB_HOST` – Remote Chroma endpoint (defaults to the shared EC2 instance).
- `CHROMADB_PORT` – Remote Chroma port (defaults to `80`).
- `CHROMADB_AUTH_TOKEN` – Optional Bearer token when the service requires authentication.
- `EMBEDDING_SERVICE_URL` – Backend override (defaults to `http://localhost:6000`).

API endpoints:

- `POST /embed` – Returns dense embeddings for supplied texts.
- `POST /query` – Queries region-specific Chroma collections.
- `GET /collections/{region}/count` – Retrieves document counts.

---

## Local Testing & Validation

```python
from common.embedding_helper import embed_batch, get_chromadb_client

REGION = "us"  # swap to "sg" for SSO
COLLECTION = "us_embeddings" if REGION == "us" else "sg_embeddings"

client = get_chromadb_client(REGION, f"chromadb_{REGION}")
collection = client.get_collection(name=COLLECTION)

query_texts = [
    "Which chemical was classified as a substance of very high concern under EU Decision 2019/1194?",
    "On what date did EU Regulation 402/2010 become effective?",
]
embeddings = embed_batch(query_texts, batch_size=2)
results = collection.query(query_embeddings=embeddings, n_results=1)
print(results["documents"])
```

`get_chromadb_client` now returns a remote `chromadb.HttpClient`, so these
commands operate directly against the shared EC2-hosted collections.

- Update `query_texts` to align with the dataset you are validating.
- Use the returned `documents` to confirm that recently ingested material is retrievable.

---

## Database Connection (psql)

```bash
psql -h reg-guru.c3my688ou3oy.ap-southeast-1.rds.amazonaws.com -p 5433 -U master -d postgres
```

---

## Adding Another Pipeline

- Define dataset-specific constants in a scraper subclass and expose `self.s3_obj` so downstream stages resolve PDF storage correctly.
- Derive a processor that points `BaseProcessor.DATASET_KEY` to the same storage root used by the scraper and promotes bronze rows to `silver.metadata`.
- Implement an embedder function that accepts `{content, metadata}` batches and persists to a dedicated Chroma collection (or your vector store of choice).
- Register the new pipeline in `src/pipelines/run_all.py` to participate in the multi-region orchestrator.
- Keep shared utilities in `src/common/` to minimise duplication across jurisdictions.
