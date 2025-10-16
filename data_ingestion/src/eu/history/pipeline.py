from typing import override
from common.BasePipeline import BasePipeline
from common.Embedder import Embedder
from eu.history.scraper import EUHistoryIngestor
from eu.history.processor import EUHistoryProcessor

class EUHistoryPipeline(BasePipeline):
    """EU pipeline implementation."""

    def __init__(self, process_batch_size=2):
        super().__init__()
        self.ds_code="eu"
        self.process_batch_size=process_batch_size
        self.scraper = EUHistoryIngestor(
            ds_name="eurlex history",
            ds_code=self.ds_code,
            ds_description="European Union official publications and legal (historical data in searching for Eurovoc 24 Finance)"
        )
        self.processor = EUHistoryProcessor(ds_code=self.ds_code, batch_size=self.process_batch_size)
        self.embedder = Embedder(self.ds_code)
        

    def ingest(self):
        new_entries_num = self.scraper.run()
        print(f"✅ EU Feed ingestion completed. Received {new_entries_num} items.")
        return

    def process(self):
        log_id = self.scraper.get_log_id()
        return self.processor.run(log_id)

    def embed(self, minibatch):
        self.embedder.embed_and_add_documents(minibatch)

    @override
    def run(self, log_id):
        # self.embedder.delete_chromadb_collection(self.ds_code+"_embeddings")
        count = 1
        for minibatch in self.processor.run(log_id):
            print("Embed batch ", count)
            self.embed(minibatch)
            count += 1

if __name__ == "__main__":
    pipeline = EUHistoryPipeline(process_batch_size=4)
    pipeline.run(100)
    # embed batch 61 finished
    # No PP4Contents from document:  data_ingestion/raw/eu/eurlex-feed/100/32008R0271.xml
    # No texts to process [data_ingestion/raw/eu/eurlex-feed/100/32008R0271.xml]