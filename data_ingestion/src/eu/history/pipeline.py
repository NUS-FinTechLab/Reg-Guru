from common.BasePipeline import BasePipeline
from scraper import EUHistoryIngestor
from processor import EUHistoryProcessor
from embedder import EUFeedEmbedder

class EUHistoryPipeline(BasePipeline):
    """EU pipeline implementation."""

    def __init__(self, process_batch_size=12):
        super().__init__()
        self.ds_code="eu"
        self.process_batch_size=process_batch_size
        self.scraper = EUHistoryIngestor(
            ds_name="eurlex history",
            ds_code=self.ds_code,
            ds_description="European Union official publications and legal (historical data in searching for Eurovoc 24 Finance)"
        )
        self.processor = EUHistoryProcessor(ds_code=self.ds_code, batch_size=self.process_batch_size)
        # self.embedder = EUFeedEmbedder("eu_feeds")
        

    def ingest(self):
        new_entries_num = self.scraper.run()
        print(f"✅ EU Feed ingestion completed. Received {new_entries_num} items.")
        return

    def process(self):
        log_id = self.scraper.get_log_id()
        return self.processor.run(log_id)

    def embed(self):
        pass

if __name__ == "__main__":
    pipeline = EUHistoryPipeline()
    pipeline.run()