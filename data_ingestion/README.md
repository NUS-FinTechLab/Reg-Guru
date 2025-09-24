# FinCEN Data Pipeline

This directory contains the FinCEN (Financial Crimes Enforcement Network) data ingestion pipeline that processes regulatory documents and embeds them into a vector database for RAG applications.

## Overview

The FinCEN pipeline uses the BGE-M3 embedding model from FlagEmbedding to create high-quality vector embeddings of financial regulatory documents. This pipeline consists of:

- **Scraper**: Downloads and extracts FinCEN regulatory documents
- **Processor**: Cleans and preprocesses the extracted text data
- **Embedder**: Converts documents into vector embeddings using BGE-M3
- **Pipeline**: Orchestrates the entire ingestion workflow

## Python Environment

This pipeline uses a dedicated virtual environment named `.venv-bgem3` with specialized dependencies for embedding generation and document processing.

### Setting up the Environment

1. **Activate the existing environment**:

   ```bash
   source .venv-bgem3/bin/activate
   ```

2. **Or create a new environment** (if needed):
   ```bash
   python -m venv .venv-bgem3
   source .venv-bgem3/bin/activate
   pip install -r requirements.txt
   ```

### Key Dependencies

- **FlagEmbedding**: BGE-M3 multilingual embedding model
- **ChromaDB**: Vector database for storing embeddings
- **Transformers**: Hugging Face transformers library
- **Sentence-Transformers**: Sentence embedding utilities
- **Torch**: PyTorch for deep learning operations
- **CUDA Support**: GPU acceleration for embedding generation

## Usage

1. **Activate the environment**:

   ```bash
   source .venv-bgem3/bin/activate
   ```

2. **Run the pipeline**:
   ```python
   python3 pipeline.py
   ```

## Configuration

- **Collection Name**: `fincen_embeddings`
- **Chunk Size**: 1000 characters
- **Chunk Overlap**: 200 characters
- **Embedding Model**: BGE-M3 (multilingual)

## Testing

   ```python
   chromadb_client = get_testing_chromadb_client('us', 'chromadb_fincen')
   test_collection = chromadb_client.get_collection(name=FINCEN_COLLECTION_NAME)
   query_texts=[
      "Which chemical was classified as a substance of very high concern for its endocrine-disrupting effects under the EU Commission Implementing Decision 2019/1194?",
      "On what date did EU Regulation 402/2010 become effective?"
   ]

   embedded_query = embed_batch(query_texts, batch_size=2)
   results = test_collection.query(
      query_embeddings=embedded_query,
      n_results=1
   )

   print(results['documents'])
    ```
## Notes for Developers

- The venv is used because of a compatibility issue in BgeM3 embedding model since it's not supporting NumPy >= 2.
```

## Database Connection in Terminal
   ```bash
   psql -h reg-guru.c3my688ou3oy.ap-southeast-1.rds.amazonaws.com -p 5433 -U master -d postgres
   ```