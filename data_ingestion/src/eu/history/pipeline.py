from typing import override

from common.BasePipeline import BasePipeline
from common.embedding_helper import embed_and_add_documents
from eu.history.scraper import EUHistoryIngestor
from eu.history.processor import EUHistoryProcessor

class EUHistoryPipeline(BasePipeline):
    """EU History pipeline implementation."""
    """Althought this pipeline has a different ds_name from the EUFeedPipeline, raw data are ingested to the same table feeds_eu_eurlex"""
    
    DEFAULT_DS_NAME = "eu_eurlex_history"
    DEFAULT_DS_CODE = "eu"
    DEFAULT_DS_DESC = "European Union official publications and legislation (historical data in the Eurovoc 24 Finance search)"

    def __init__(
        self,
        ds_name: str = DEFAULT_DS_NAME,
        ds_code: str = DEFAULT_DS_CODE,
        ds_description: str = DEFAULT_DS_DESC,
        process_batch_size: int = 4,
        test_mode: bool = False
    ) -> None:
        self.ds_name = ds_name if not test_mode else f"{ds_name}_test"
        self.ds_code = ds_code
        self.ds_description = ds_description if not test_mode else f"{ds_description} (test)"
        self.process_batch_size=process_batch_size
        self.scraper = EUHistoryIngestor(ds_name=self.ds_name, ds_code=self.ds_code, ds_description=self.ds_description, test_mode=test_mode)
        self.processor = EUHistoryProcessor(
            ds_name=self.scraper.get_data_source_name(),
            batch_size=self.process_batch_size,
            test_mode=test_mode
        )
        self.test_mode = test_mode

    def ingest(self):
        new_entries_num = self.scraper.run()
        print(f"✅ EU History ingestion completed. Received {new_entries_num} items.")
        return new_entries_num

    def process(self):
        log_id = self.scraper.get_log_id()
        return self.processor.run(log_id)

    def embed(self, minibatch):
        if not minibatch:
            return
        if self.test_mode:
            embed_and_add_documents(minibatch, self.ds_code, collection_name="test")
        else:
            embed_and_add_documents(minibatch, self.ds_code)
        return

    # @override
    # def run(self, log_id):
    #     # self.embedder.delete_collection(self.ds_code+"_embeddings")
    #     count = 1
    #     for minibatch in self.processor.run(log_id):
    #         print("Embed batch ", count)
    #         self.embed(minibatch)
    #         count += 1

if __name__ == "__main__":
    pipeline = EUHistoryPipeline()
    pipeline.run()
    # pipeline.run(118)