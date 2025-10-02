import os
import sys

# Add the parent directories to the Python path to resolve imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, src_dir)

from common import IngestionPipeline
from sg.sso.scraper import SsoScraper
from sg.sso.process import SsoProcessor

class SsoPipeline(IngestionPipeline):
    """SSO-specific pipeline implementation with FlagEmbedding support."""
    
    def __init__(self, process_batch_size=12):
        self.process_batch_size=process_batch_size
        self.scraper = SsoScraper(
            ds_name="sso acts",
            ds_code="sg",
            ds_description="Singapore Statutes Online official acts"
        )
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