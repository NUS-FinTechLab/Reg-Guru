from datetime import datetime

from ...common import IngestionPipeline
from .embedding import embed_into_chromadb
from .scraper import FincenScraper
from .process import process_fincen_data

class FincenPipeline(IngestionPipeline):
    """FinCEN-specific pipeline implementation with FlagEmbedding support."""

    def __init__(self, process_batch_size=12):
        self.process_batch_size = process_batch_size
        self.scraper = FincenScraper()
        self._raw_data = None
        self._run_id = None

    def ingest(self):
        """Download or read raw data using the scraper."""
        print("📥 Starting FinCEN data ingestion...")
        self._raw_data = None
        self._run_id = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        self._raw_data = self.scraper.scrape(run_id=self._run_id)
        item_count = len(self._raw_data.get("documents", [])) if self._raw_data else 0
        print(f"✅ FinCEN ingestion completed. Retrieved {item_count} items.")
        return

    def process(self):
        """Convert raw data into structured docs (list of dicts)."""
        if not self._raw_data:
            raise RuntimeError("No raw data available. Call ingest() before process().")

        print("🔄 Processing FinCEN raw data...")
        processed_data = process_fincen_data(self._raw_data)
        doc_count = len(processed_data) if processed_data else 0
        print(f"✅ FinCEN processing completed. Generated {doc_count} documents.")

        if not processed_data:
            return iter([])

        def batch_iterator():
            batch = []
            for doc in processed_data:
                batch.append(doc)
                if len(batch) == self.process_batch_size:
                    yield batch
                    batch = []
            if batch:
                yield batch

        return batch_iterator()
    
    def embed(self, docs):
        """Embed documents into Chroma or other vector DB."""
        print(f"🔗 Embedding {len(docs) if docs else 0} FinCEN documents...")
        embed_into_chromadb(docs)
        print("✅ FinCEN embedding completed.")

if __name__ == "__main__":
    pipeline = FincenPipeline()
    pipeline.run()
