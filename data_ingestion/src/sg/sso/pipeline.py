from ...common.BasePipeline import BasePipeline
from .embedder import embed_into_chromadb
from .processor import SsoProcessor
from .scraper import SsoScraper


class SsoPipeline(BasePipeline):
    """SSO-specific pipeline implementation with FlagEmbedding support."""

    def __init__(self, process_batch_size=12):
        super().__init__()
        self.process_batch_size = process_batch_size
        self.scraper = SsoScraper()
        self.processor = SsoProcessor(
            ds_code=self.scraper.DEFAULT_DS_CODE, batch_size=self.process_batch_size
        )
        self.latest_log_id = None

    def ingest(self):
        """Download or read raw data using the scraper."""
        print("📥 Starting SSO data ingestion...")
        new_entries_num = self.scraper.run()
        self.latest_log_id = self.scraper.get_log_id()
        print(f"✅ SSO ingestion completed. Logged {new_entries_num} new items.")
        return

    def process(self):
        """Convert raw data into structured docs (list of dicts)."""
        if not self.latest_log_id:
            print("⚠️ No ingestion log id available; skipping processing phase.")
            return iter([])

        print("🔄 Processing SSO raw data...")
        return self.processor.run(self.latest_log_id)

    def embed(self, minibatch):
        """Embed documents into Chroma or other vector DB."""
        if not minibatch:
            return
        print(f"🔗 Embedding {len(minibatch)} SSO documents...")
        embed_into_chromadb(minibatch)
        print("✅ Embedding step completed.")


if __name__ == "__main__":
    pipeline = SsoPipeline()
    pipeline.run()
