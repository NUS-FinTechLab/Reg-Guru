import sys
import os

# Add the parent directories to the Python path to resolve imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, src_dir)

from common.pipeline_base import IngestionPipeline
from scraper import FincenScraper
from process import process_fincen_data

class FincenPipeline(IngestionPipeline):
    """FinCEN-specific pipeline implementation."""
    
    def __init__(self):
        self.scraper = FincenScraper()
    
    def ingest(self):
        """Download or read raw data using the scraper."""
        raw_data = self.scraper.scrape()
        return raw_data
    
    def process(self, raw_data):
        """Convert raw data into structured docs (list of dicts)."""
        processed_data = process_fincen_data(raw_data)
        return processed_data
    
    def embed(self, docs):
        """Embed documents into Chroma or other vector DB."""
        print(f"Embedding {len(docs)} documents")
        for i, doc in enumerate(docs):
            print(f"Document {i+1}: {doc['source']} ({doc['type']})")


if __name__ == "__main__":
    pipeline = FincenPipeline()
    pipeline.run()
