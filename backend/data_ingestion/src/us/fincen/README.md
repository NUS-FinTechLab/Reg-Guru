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
   from pipeline import FincenPipeline
   
   pipeline = FincenPipeline()
   pipeline.ingest()
   ```

3. **Individual components**:
   ```python
   # Scraping
   from scraper import FincenScraper
   scraper = FincenScraper()
   documents = scraper.scrape()
   
   # Processing
   from process import process_fincen_data
   processed_docs = process_fincen_data(documents)
   
   # Embedding
   from embedding import embed_into_chromadb
   embed_into_chromadb(processed_docs)
   ```

## Configuration

- **Collection Name**: `fincen_embeddings`
- **Chunk Size**: 1000 characters
- **Chunk Overlap**: 200 characters
- **Embedding Model**: BGE-M3 (multilingual)

## Hardware Requirements

- **GPU**: Recommended for faster embedding generation (CUDA-compatible)
- **Memory**: Minimum 8GB RAM, 16GB+ recommended for large document sets
- **Storage**: Sufficient space for raw documents and vector database

## Notes for Developers

- This environment is specifically tuned for BGE-M3 embeddings
- GPU acceleration is enabled through CUDA packages
- The pipeline integrates with the common embedding helper utilities
- ChromaDB is used as the vector store backend
- Documents are chunked with overlap to maintain context continuity

## Troubleshooting

- **CUDA Issues**: Ensure CUDA drivers are installed and compatible
- **Memory Issues**: Reduce batch size in embedding operations
- **Import Errors**: Verify the environment is activated and dependencies are installed