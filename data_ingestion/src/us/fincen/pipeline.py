from ...common.BasePipeline import BasePipeline
from ...common.embedding_helper import embed_and_add_documents
from .processor import FincenProcessor
from .scraper import FincenScraper


class FincenPipeline(BasePipeline):
    """FinCEN-specific pipeline mirroring the shared scrape → process → embed flow."""
    DEFAULT_DS_NAME = "us_fincen"
    DEFAULT_DS_CODE = "us"
    DEFAULT_DS_DESC = "FinCEN Advisories and Bulletins"

    def __init__(
        self,
        ds_name: str = DEFAULT_DS_NAME,
        ds_code: str = DEFAULT_DS_CODE,
        ds_description: str = DEFAULT_DS_DESC,
        process_batch_size: int = 12,
        test_mode: bool = False
    ) -> None:
        self.ds_name = ds_name if not test_mode else f"{ds_name}_test"
        self.ds_code = ds_code
        self.ds_description = ds_description if not test_mode else f"{ds_description} (test)"
        self.process_batch_size=process_batch_size
        self.scraper = FincenScraper(ds_name=self.ds_name, ds_code=self.ds_code, ds_description=self.ds_description, test_mode=test_mode)
        self.processor = FincenProcessor(ds_name=self.ds_name, batch_size=self.process_batch_size, test_mode=test_mode)
        self.test_mode = test_mode
        self.latest_log_id = None

    def ingest(self) -> None:
        """Download raw advisories and persist their metadata."""
        print("📥 Starting FinCEN data ingestion...")
        new_entries_num = self.scraper.run()
        self.latest_log_id = self.scraper.get_log_id()
        print(f"✅ FinCEN ingestion completed. Logged {new_entries_num} new items.")
        return new_entries_num

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
        if self.test_mode:
            embed_and_add_documents(minibatch, self.ds_code, collection_name="test")
        else:
            embed_and_add_documents(minibatch, self.ds_code)
        print("✅ Embedding step completed.")
        return


if __name__ == "__main__":
    pipeline = FincenPipeline(test_mode=True)
    pipeline.run()
