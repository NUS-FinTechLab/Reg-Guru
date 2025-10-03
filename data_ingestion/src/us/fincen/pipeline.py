from ...common import IngestionPipeline
from .embedding import embed_into_chromadb
from .scraper import FincenScraper
from .process import process_fincen_data

class FincenPipeline(IngestionPipeline):
    """FinCEN-specific pipeline implementation with FlagEmbedding support."""
    
    def __init__(self):
        self.scraper = FincenScraper()

    def ingest(self):
        """Download or read raw data using the scraper."""
        print("📥 Starting FinCEN data ingestion...")
        raw_data = self.scraper.scrape()
        print(f"✅ FinCEN ingestion completed. Retrieved {len(raw_data) if raw_data else 0} items.")
        return raw_data
    
    def process(self, raw_data):
        """Convert raw data into structured docs (list of dicts)."""
        print("🔄 Processing FinCEN raw data...")
        processed_data = process_fincen_data(raw_data)
        print(f"✅ FinCEN processing completed. Generated {len(processed_data) if processed_data else 0} documents.")
        return processed_data
    
    def embed(self, docs):
        """Embed documents into Chroma or other vector DB."""
        print(f"🔗 Embedding {len(docs) if docs else 0} FinCEN documents...")
        embed_into_chromadb(docs)
        print("✅ FinCEN embedding completed.")

if __name__ == "__main__":
    pipeline = FincenPipeline()
    pipeline.run()
