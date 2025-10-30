# Ingestion Pipelines

This directory houses the ingestion stacks that scrape regulatory sources, normalize documents, and embed text chunks into vector stores for Retrieval-Augmented Generation (RAG) workloads. Shared base classes in `src/common/` keep core logic reusable so new jurisdictions can plug into the same scrape → process → embed flow.

Currently implemented pipelines (historical pipelines are designed to only run once during the first set-up):

- **FinCEN (US)** – Financial Crimes Enforcement Network releases.
- **SSO (SG)** – Singapore Statutes Online acts.
- **EURLEX FEED (EU)** - European Union Regulations on Finance.
- **EURLEX HISTORY (EU)** - European Union Regulations on Finance (Historical Documents)

## 1. Setup
- Create a new environment for data ingestion with requirement.txt (if needed):
   ```bash
   pip install -r requirements.txt
   # Or faster pip through Tsinghua mirrors: pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```
- **Activate** the environment.
- Ensure `embedding service` is running. There is no need to install embedding related heavy packages inside the data ingestion environment.

## 2. Pipeline Architecture

### Stage 1 – Scrape (`*_Scraper`)

- `BaseScraper` provides throttled HTML requests, pagination helpers, and logging utilities in `src/common/`.
- Dataset scrapers (`FincenScraper`, `SsoScraper`) fetch listing/browse pages via `_request_html`, follow `_next_page_url`, and deduplicate records using `doc_id`.
- Detail pages supply authoritative metadata (titles, published/valid dates, PDF links).
- `log_into_database` ensures the bronze table exists for the dataset and inserts/updates rows under a unique ingestion `log_id`.
- `store_documents` downloads canonical PDFs into `data_ingestion/raw/<region>/<dataset>/<log_id>/` or into S3 when `S3_BUCKET_NAME` is set.

### Stage 2 – Process (`*_Processor`)

- `BaseProcessor` promotes bronze rows into the silver tier once per run through `clean_metadata`.
- `extract_metadata` returns the cleaned metadata in the silver tier assisting document embedding.
- `extract_texts` and `clean_texts ` extracts plain texts from the given document and clean them respectively.
- `_process_a_document` applies the shared text cleaner and attaches metadata before yielding batches through `run(batch_size)`.

### Stage 3 – Embed (`embed_into_chromadb`)

- `embed_and_add_documents` relies on the embedding service and applies the shared text splitter, embedder, and chromadb client, inserting or updating the document embeddings in the vector store.

### Stage 4 – Orchestrate (`*_Pipeline`)

- Pipelines inherit from `BasePipeline`, exposing `ingest()`, `process(log_id)`, `embed(minibatch)`, and `run()`.
- `ingest()` runs the scraper and returns the number of inserted/updated rows.
- `process(log_id)` streams normalized document batches from the matching processor.
- `embed(minibatch)` forwards batches to the embedding service and logs completion.
- `run()` chains the stages, enabling standalone execution or multi-region orchestration via `src/pipelines/run_all.py`.

### Shared Services & Utilities

- `src/common/embedding_helper.py` provides helpers such as `embed_batch`, `get_chromadb_client`, and collection accessors shared across datasets.
- `src/pipelines/init_database.py` allows you to initialise the database with a basic structure.

## 3. Dataset Quick Reference

| Dataset | Module | Source | Bronze Tier Table | S3 back-up storage | Jurisdiction | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| FinCEN (US) | `src/us/fincen/` | Advisory listings on fincen.gov | `bronze.feeds_us_fincen` | `data_ingestion/raw/us/fincen/<log_id>/` | `us` | Detail-page crawl captures the first advisory PDF; duplicates skipped by `doc_id`. |
| SSO (SG) | `src/sg/sso/` | Singapore Statutes Online browse pages | `bronze.feeds_sg_sso` | `data_ingestion/raw/sg/sso/<log_id>/` | `sg` | Flags superseded/missing statutes and records effective/valid dates from act detail pages. |
| EURLEX FEED (EU) | `src/eu/feed/` | Finance regulations on EUR-LEX | `bronze.feeds_eu_eurlex` | `data_ingestion/raw/eu/eurlex-feed/<log_id>/` | `eu` | `CELEX number` is the unique id used in the EUR-LEX system |
| EURLEX HISTORY (EU) | `src/eu/history/` | Finance regulations on EUR-LEX (History Documents) | `bronze.feeds_eu_eurlex` | `data_ingestion/raw/eu/eurlex-feed/<log_id>/` | `eu` | `CELEX number` is the unique id used in the EUR-LEX system |

## 4. Running Pipelines

**Activate the dedicated environment for data ingestion before running.**

```bash
# Run a single pipeline
python3 src/<jurisdiction>/<source>/pipeline.py

# Or run all sequentially
python3 src/pipelines/run_all.py
```

- Each run prints ingestion counts and the Chroma destination for embedded chunks.
- Provide `S3_BUCKET_NAME` to push documents to object storage.
- Override `CHROMADB_HOST` or `CHROMADB_PORT` to target a different Chroma deployment.
- `main` in `run_all.py` requires two arguments: `history` and `test_mode`.
    - Always set `history = False` if you run / schedule the pipelines to check updates of existing documents. Only set `history = True` when you run the pipelines for the first time to initialise the database.
    - Set `test_mode = True` to test if the pipelines work properly by absorbing a small scale of documents. If the test mode is enabled:
        - Data in the bronze / silver tier is stored to the test tables in the same tiers.
        - Data sources are marked as test data sources.
        - Embeddings are stored to the 'test' collection in the same ChromaDB Client, instead of the default collection ('reg-guru-embeddings').

## 5. Real-Time Embedding & Query Service

A FastAPI app wraps the embedder and ChromaDB queries as a re-usable long-run separate service so other services do not need to manage the embedding environment. 

**In a separate terminal, activate the embedding service environment, then**:

```bash
cd src
uvicorn common.embedding_service:app --host 0.0.0.0 --port 6000 --reload
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
- `POST /query` – Queries Chroma collections with specific filters.

## 6. Local Testing & Validation

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

## 7. Database Connection (psql)

```bash
# Default / production database postgres
psql -h reg-guru.c3my688ou3oy.ap-southeast-1.rds.amazonaws.com -p 5433 -U master -d postgres
```
Key in the password for the user.

## 8. Adding Another Pipeline

- Define dataset-specific constants in a scraper subclass and expose `self.s3_obj` so downstream stages resolve PDF storage correctly.
- Derive a processor that points `BaseProcessor.DATASET_KEY` to the same storage root used by the scraper and promotes bronze data to the silver tier.
- Implement an embedder function that accepts `{content, metadata}` batches and persists to a dedicated Chroma collection (or your vector store of choice).
- Register the new pipeline in `src/pipelines/run_all.py` to participate in the multi-region orchestrator.
- Keep shared utilities in `src/common/` to minimise duplication across jurisdictions.
