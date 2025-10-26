# Ingestion Pipelines

This directory houses the ingestion stacks that scrape regulatory sources, normalize documents, and embed text chunks into vector stores for Retrieval-Augmented Generation (RAG) workloads. Shared base classes in `src/common/` keep core logic reusable so new jurisdictions can plug into the same scrape → process → embed flow.

Currently implemented pipelines:

- **FinCEN (US)** – Financial Crimes Enforcement Network releases.
- **SSO (Singapore)** – Singapore Statutes Online acts.
- **EUR-LEX (EU)** - European Union Regulations on Finance.

---

## 1. Setup
Create a new environment (if needed):
   ```bash
   # In venv: this will create a venv environment.
   # Create a .venv-bgem3 folder inside the project
   python -m venv .venv-bgem3
   source .venv-bgem3/bin/activate
   pip install -r requirements.txt
   # Or faster pip through Tsinghua mirrors: pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```
   ```bash
   # In conda: this will create a conda environment
   conda create -n reg-embed
   conda activate reg-embed
   pip install -r requirements.txt
   # Or faster pip through Tsinghua mirrors: pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

## 2. Key Dependencies

- **ChromaDB** – Persistent vector store
- **Transformers / Sentence-Transformers** – Embedding models and text preprocessing utilities
- **PyTorch** – Backing framework for embeddings (with CUDA support if available)

---

## 3. Pipeline Architecture

### Stage 1 – Scrape (`*_Scraper`)
1. **Activate the environment**:
   ```bash
   # In venv:
   source .venv-bgem3/bin/activate
   ```
   ```bash
   # Or in conda:
   conda activate reg-embed
   ```

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
- `embed_into_chromadb` persists chunk text, embeddings, and metadata into the shared `CHROMADB_COLLECTION` while tagging rows with the region-specific `embedding_name` (e.g., `sg_embeddings`).

### Stage 4 – Orchestrate (`*_Pipeline`)

- Pipelines inherit from `BasePipeline`, exposing `ingest()`, `process(log_id)`, `embed(minibatch)`, and `run()`.
- `ingest()` runs the scraper and returns both `log_id` and the number of inserted/updated rows.
- `process(log_id)` streams normalized document batches from the matching processor.
- `embed(minibatch)` forwards batches to the embedding helper and logs completion.
- `run()` chains the stages, enabling standalone execution or multi-region orchestration via `src/pipelines/run_all.py`.

### Shared Services & Utilities

- `src/common/embedding_helper.py` provides helpers such as `embed_batch`, `get_testing_chromadb_client`, and collection accessors shared across datasets.
- `src/pipelines/init_database.py` provisions bronze/silver tables for local development.

---

## 4. Dataset Quick Reference

| Dataset | Module | Source | Bronze table | S3 back-up storage | Chroma collection | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| FinCEN (US) | `src/us/fincen/` | Advisory listings on fincen.gov | `bronze.feeds_us_fincen` | `data_ingestion/raw/us/fincen/<log_id>/` | `us_embeddings` (remote) | Detail-page crawl captures the first advisory PDF; duplicates skipped by `doc_id`. |
| SSO (Singapore) | `src/sg/sso/` | Singapore Statutes Online browse pages | `bronze.feeds_sg_sso` | `data_ingestion/raw/sg/sso/<log_id>/` | `sg_embeddings` (remote) | Flags superseded/missing statutes and records effective/valid dates from act detail pages. |
| EUR-LEX (EU) | `src/eu/feed/` | Finance regulations on EUR-LEX | `bronze.feeds_eu` | `data_ingestion/raw/eu/eurlex-feed/<log_id>/` | `eu_embeddings` (`chroma/eu/chromadb_eu`) | `CELEX number` is the unique id used in the EUR-LEX system |

---

## 5. Running Pipelines

**Activate the dedicated environment for data ingestion before running.**

```bash
# Fincen Advisories
python3 src/us/fincen/pipeline.py

# Singapore Statutes Online
python3 src/sg/sso/pipeline.py

# Or run both sequentially
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
uvicorn embedding_service.embedding_service:app --host 0.0.0.0 --port 6000 --reload
```

 Environment variables:

- `EMBEDDER_MODEL` – Override the default `BAAI/bge-m3`.
- `CHROMADB_HOST` – Remote Chroma endpoint (defaults to the shared EC2 instance).
- `CHROMADB_PORT` – Remote Chroma port (defaults to `80`).
- `CHROMADB_COLLECTION` – Shared collection name (defaults to `reg_guru_embeddings`).
- `CHROMADB_AUTH_TOKEN` – Optional Bearer token when the service requires authentication.
- `EMBEDDING_SERVICE_URL` – Backend override (defaults to `http://localhost:6000`).

API endpoints:

- `POST /embed` – Returns dense embeddings for supplied texts.
- `POST /query` – Queries region-specific Chroma collections.

---

## Local Testing & Validation

```python
from common.embedding_helper import embed_batch, get_chromadb_client, get_default_collection

REGION = "us"  # swap to "sg" for SSO
EMBEDDING_TAG = "us_embeddings" if REGION == "us" else "sg_embeddings"

client = get_chromadb_client()
collection = get_default_collection()

query_texts = [
    "Which chemical was classified as a substance of very high concern under EU Decision 2019/1194?",
    "On what date did EU Regulation 402/2010 become effective?",
]
embeddings = embed_batch(query_texts, batch_size=2)
results = collection.query(
    query_embeddings=embeddings,
    n_results=1,
    where={"embedding_name": EMBEDDING_TAG},
)
print(results["documents"])
```

`get_chromadb_client` now returns a remote `chromadb.HttpClient`, and
`get_default_collection` yields the shared collection. Filtering by the
`embedding_name` metadata keeps region-specific queries isolated.

- Update `query_texts` to align with the dataset you are validating.
- Use the returned `documents` to confirm that recently ingested material is retrievable.

---

## 7. Database Connection (psql)

```bash
psql -h reg-guru.c3my688ou3oy.ap-southeast-1.rds.amazonaws.com -p 5433 -U master -d postgres
```

---

## 8. Adding Another Pipeline

- Define dataset-specific constants in a scraper subclass and expose `self.s3_obj` so downstream stages resolve PDF storage correctly.
- Derive a processor that points `BaseProcessor.DATASET_KEY` to the same storage root used by the scraper and promotes bronze rows to `silver.metadata`.
- Implement an embedder function that accepts `{content, metadata}` batches and persists to a dedicated Chroma collection (or your vector store of choice).
- Register the new pipeline in `src/pipelines/run_all.py` to participate in the multi-region orchestrator.
- Keep shared utilities in `src/common/` to minimise duplication across jurisdictions.
