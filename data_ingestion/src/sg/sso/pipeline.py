from common.BasePipeline import BasePipeline 
from scraper import SsoScraper
from processor import SsoProcessor

class SsoPipeline(BasePipeline):
    """SSO-specific pipeline implementation with FlagEmbedding support."""
    
    def __init__(self, process_batch_size=12):
        super().__init__()
        self.ds_code="sg"
        self.process_batch_size=process_batch_size
        self.scraper = SsoScraper(
            ds_name="sso acts",
            ds_code=self.ds_code,
            ds_description="Singapore Statutes Online official acts"
        )
        self.processor = SsoProcessor(ds_code=self.ds_code, batch_size=self.process_batch_size)

    def ingest(self):
        """Download or read raw data using the scraper."""
        print("📥 Starting SSO data ingestion...")
        new_entries_num = self.scraper.run()
        print(f"✅ SSO ingestion completed. Received {new_entries_num} items.")
        return
    
    def process(self):
        """Convert raw data into structured docs (list of dicts)."""
        print("🔄 Processing SSO raw data...")
        log_id = self.scraper.get_log_id()
        return self.processor.run(log_id)
    
    def embed(self, minibatch):
        """Embed documents into Chroma or other vector DB."""
        print(f"🔗 Embedding SSO documents...")
        # Connect to embedding service to embed.
        
        pass


if __name__ == "__main__":
    pipeline = SsoPipeline()
    pipeline.run()