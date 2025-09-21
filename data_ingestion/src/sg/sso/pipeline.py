import sys
import os

# Add the parent directories to the Python path to resolve imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, src_dir)

from common import IngestionPipeline
from sg.sso.embedding import embed_into_chromadb
from sg.sso.scraper import SsoScraper
from sg.sso.process import process_sso_data

class SsoPipeline(IngestionPipeline):
    """SSO-specific pipeline implementation with FlagEmbedding support."""
    
    def __init__(self):
        self.scraper = SsoScraper()

    def ingest(self):
        """Download or read raw data using the scraper."""
        print("📥 Starting SSO data ingestion...")
        raw_data = self.scraper.scrape()
        print(f"✅ SSO ingestion completed. Retrieved {len(raw_data) if raw_data else 0} items.")
        return raw_data
    
    def process(self, raw_data):
        """Convert raw data into structured docs (list of dicts)."""
        print("🔄 Processing SSO raw data...")
        processed_data = process_sso_data(raw_data)
        print(f"✅ SSO processing completed. Generated {len(processed_data) if processed_data else 0} documents.")
        return processed_data
    
    def embed(self, docs):
        """Embed documents into Chroma or other vector DB."""
        print(f"🔗 Embedding {len(docs) if docs else 0} SSO documents...")
        embed_into_chromadb(docs)
        print("✅ SSO embedding completed.")

if __name__ == "__main__":
    pipeline = SsoPipeline()
    pipeline.run()