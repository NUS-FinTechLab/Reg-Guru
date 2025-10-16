from ...common.BasePipeline import BasePipeline
from .embedding import embed_into_chromadb
from .processor import FincenProcessor
from .scraper import FincenScraper


class FincenPipeline(BasePipeline):
    """FinCEN-specific pipeline mirroring the shared scrape → process → embed flow."""

    def __init__(self, process_batch_size: int = 12) -> None:
        super().__init__()
        self.process_batch_size = process_batch_size
        self.scraper = FincenScraper()
        self.processor = FincenProcessor(
            ds_code=self.scraper.DEFAULT_DS_CODE,
            batch_size=self.process_batch_size,
        )
        self.latest_log_id = None

    def ingest(self) -> None:
        """Download raw advisories and persist their metadata."""
        print("📥 Starting FinCEN data ingestion...")
        new_entries = self.scraper.run()
        self.latest_log_id = self.scraper.get_log_id()
        print(f"✅ FinCEN ingestion completed. Logged {new_entries} new items.")

    def process(self):
        """Convert raw advisories into cleaned document batches."""
        if not self.latest_log_id:
            print("⚠️ No ingestion log id available; skipping processing phase.")
            return iter([])

        print("🔄 Processing FinCEN raw data...")
        return self.processor.run(self.latest_log_id)

    def embed(self, minibatch):
        """Embed processed batches into the FinCEN Chroma collection."""
        if not minibatch:
            return
        print(f"🔗 Embedding {len(minibatch)} FinCEN documents...")
        embed_into_chromadb(minibatch)
        print("✅ FinCEN embedding completed.")


if __name__ == "__main__":
    pipeline = FincenPipeline()
    pipeline.run()
