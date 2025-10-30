from common.BasePipeline import BasePipeline
from common.embedding_helper import embed_and_add_documents
from eu.feed.scraper import EUFeedIngestor
from eu.feed.processor import EUFeedProcessor

class EUFeedPipeline(BasePipeline):
    """EU Feed pipeline implementation."""
    DEFAULT_DS_NAME = "eu_eurlex"
    DEFAULT_DS_CODE = "eu"
    DEFAULT_DS_DESC = "European Union official publications and legislation"

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
        self.scraper = EUFeedIngestor(ds_name=self.ds_name, ds_code=self.ds_code, ds_description=self.ds_description, test_mode=test_mode)
        self.processor = EUFeedProcessor(ds_name=self.ds_name, batch_size=self.process_batch_size, test_mode=test_mode)
        self.test_mode = test_mode
        

    def ingest(self):
        new_entries_num = self.scraper.run()
        print(f"✅ EU Feed ingestion completed. Received {new_entries_num} items.")
        return new_entries_num

    def process(self):
        log_id = self.scraper.get_log_id()
        if log_id is None:
            raise Exception("Error ingesting: new_entries_num > 0 but log_id is None")
        else:
            return self.processor.run(log_id)

    def embed(self, minibatch):
        if not minibatch:
            return
        if self.test_mode:
            embed_and_add_documents(minibatch, self.ds_code, collection_name="test")
        else:
            embed_and_add_documents(minibatch, self.ds_code)
        return

if __name__ == "__main__":
    pipeline = EUFeedPipeline(test_mode=True)
    pipeline.run()