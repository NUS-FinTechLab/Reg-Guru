# Ingestion Pipelines

This directory houses the ingestion stacks that scrape regulatory sources, process them into structured documents, and embed text chunks into vector stores for Retrieval-Augmented Generation (RAG) workloads. The shared base classes in `src/common/` keep core logic reusable so new jurisdictions can plug into the same scrape → process → embed flow.

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

## FinCEN (US) Pipeline

The FinCEN stack lives under `src/us/fincen/` and follows the standard stages:

1. **Scraper** – Downloads FinCEN regulatory documents.
2. **Processor** – Cleans and normalises text/metadata.
3. **Embedder** – Generates BGE-M3 embeddings and writes to Chroma.
4. **Pipeline** – Orchestrates ingest → process → embed.

### Running the Pipeline

```bash
source .venv-bgem3/bin/activate
python3 src/us/fincen/pipeline.py
```

### Real-Time Embedding & Query Service

A FastAPI app wraps embedding and ChromaDB queries so the backend does not have to manage the ingestion environment.

```bash
source .venv-bgem3/bin/activate
cd src
uvicorn common.embedding_service:app --host 0.0.0.0 --port 6000 --reload
```

Environment variables:

- `EMBEDDER_MODEL` – Override the default `BAAI/bge-m3`.
- `CHROMADB_ROOT_DIR` – Custom location for Chroma persistence.
- `EMBEDDING_SERVICE_URL` – Backend URL override (defaults to `http://localhost:6000`).

API endpoints:

- `POST /embed` – Returns dense embeddings for supplied texts.
- `POST /query` – Queries region-specific Chroma collections.
- `GET /collections/{region}/count` – Retrieves document counts.

### Testing Example

```python
from common.embedding_helper import embed_batch, get_testing_chromadb_client

FINCEN_COLLECTION_NAME = "fincen_embeddings"
client = get_testing_chromadb_client("us", "chromadb_fincen")
collection = client.get_collection(name=FINCEN_COLLECTION_NAME)

query_texts = [
    "Which chemical was classified as a substance of very high concern under EU Decision 2019/1194?",
    "On what date did EU Regulation 402/2010 become effective?",
]
embeddings = embed_batch(query_texts, batch_size=2)
results = collection.query(query_embeddings=embeddings, n_results=1)
print(results["documents"])
```

### Database Connection (psql)

```bash
psql -h reg-guru.c3my688ou3oy.ap-southeast-1.rds.amazonaws.com -p 5433 -U master -d postgres
```

---

## SSO (Singapore) Pipeline

The Singapore Statutes Online pipeline (`src/sg/sso/`) mirrors the FinCEN structure, targeting the SSO browse pages. It demonstrates how to adopt the shared base classes for a new region.

### 1. Scrape – `SsoScraper`

1. **List pages** – `_request_html` fetches browse pages sequentially, respecting `PAGE_DELAY`.
2. **Row parsing** – `_extract_documents_from_page` reads the results table and captures title, statute route, and PDF URL for each act.
3. **Document metadata** – `_extract_document_metadata` visits the act detail page to capture published/valid dates.
4. **Pagination** – `_next_page_url` follows the "Next Page" button until the listing ends.
5. **Bronze logging** – `log_into_database` ensures `bronze.feeds_sg_sso` exists, flags superseded or missing statutes, and inserts new or updated rows under a fresh log id.
6. **File storage** – `store_documents` downloads every PDF either to `data_ingestion/raw/sg/sso/<log_id>/` or to an S3 bucket if `S3_BUCKET_NAME` is set.

Outputs: bronze table rows keyed by `doc_id` and PDF files grouped by ingestion `log_id`.

### 2. Process – `SsoProcessor`

1. **Silver metadata** – `clean_metadata` copies bronze rows for the run into `silver.metadata` once.
2. **Metadata retrieval** – `extract_metadata` normalises timestamps and returns the fields required to locate each PDF.
3. **PDF loading** – `extract_texts` reads the PDF from S3 or disk and returns one string per page via pdfplumber.
4. **Cleaning** – `_process_document` runs the shared `clean_texts`, merges page text, and attaches metadata.
5. **Batch yield** – `run` emits lists of `{ "content": text, "metadata": {...} }` capped at `batch_size`.

Outputs: generator of ready-to-embed document batches.

### 3. Embed – `embed_into_chromadb`

1. **Chunking** – `_split_documents` breaks each document into overlapping windows using LangChain (`CHUNK_SIZE=1000`, `CHUNK_OVERLAP=200`).
2. **Embedding** – `embed_batch` (FlagEmbedding BGE-M3) encodes chunks in groups of 16.
3. **Persistence** – Chunks, vectors, and metadata are stored in the `sg_embeddings` Chroma collection under `chroma/sg/chromadb_sg`.

Outputs: persistent Chroma collection populated with SSO chunk embeddings.

### 4. Pipeline Orchestration – `SsoPipeline`

1. `ingest()` runs the scraper and records the latest `log_id`.
2. `process()` streams batches from `SsoProcessor.run(log_id)`.
3. `embed(minibatch)` sends each batch to `embed_into_chromadb` and logs completion.
4. `run()` (from `BasePipeline`) ties the stages together by calling `ingest()`, looping over `process()`, and embedding each batch.

### Reuse Checklist

- Define dataset-specific constants in your scraper subclass and set `self.s3_obj` so downstream stages know where PDFs live.
- Use `BaseProcessor.DATASET_KEY` to point at the same storage path the scraper writes to.
- Promote bronze rows to `silver.metadata` in `clean_metadata` so other systems consume a consistent view.
- Expose a single embedder function that accepts an iterable of `{content, metadata}` items and writes to your vector store of choice.
- Register the new pipeline in `src/pipelines/run_all.py` to run it alongside existing regions.

---

With these conventions, adding another scraping pipeline is as simple as implementing region-specific subclasses and wiring them through the shared orchestration interface.
