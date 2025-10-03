from ...common import IngestionPipeline
from .scraper import SsoScraper
from .process import SsoProcessor

class SsoPipeline(IngestionPipeline):
    """SSO-specific pipeline implementation with FlagEmbedding support."""
    
    def __init__(self, process_batch_size=12):
        self.process_batch_size=process_batch_size
        self.scraper = SsoScraper()
        self.processor = SsoProcessor(self.process_batch_size)

    def ingest(self):
        """Download or read raw data using the scraper."""
        print("📥 Starting SSO data ingestion...")
        new_entries_num = self.scraper.run()
        print(f"✅ SSO ingestion completed. Retrieved {new_entries_num} items.")
        return
    
    def process(self):
        """Convert raw data into structured docs (list of dicts)."""
        print("🔄 Processing SSO raw data...")
        return self.processor.run()
    
    def embed(self, minibatch):
        """Embed documents into Chroma or other vector DB."""
        print(f"🔗 Embedding SSO documents...")
        # Connect to embedding service to embed.
        
        pass

if __name__ == "__main__":
    pipeline = SsoPipeline()
    pipeline.run()
