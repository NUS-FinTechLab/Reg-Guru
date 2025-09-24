from common.pipeline_base import IngestionPipeline
from eu.EUFeedIngestor import EUFeedIngestor
from eu.EUFeedProcessor import EUFeedProcessor
from eu.EUFeedEmbedder import EUFeedEmbedder

class EUFeedPipeline(IngestionPipeline):
    """EU pipeline implementation."""

    def __init__(self):
        super().__init__()
        self.ingestor = EUFeedIngestor("https://eur-lex.europa.eu/EN/display-feed.rss?myRssId=zqe48ppy80IwdPmk3XxQMlkGOfbi%2BE8KLQfclbDnbig%3D")
        self.processor = EUFeedProcessor()
        self.embedder = EUFeedEmbedder("eu_feeds")
        

    def ingest(self):
        self.ingestor.run()
        return

    def process(self):
        log_id = self.ingestor.get_log_id()
        self.processor(log_id)
        return

    def embed(self):
        log_id = self.ingestor.get_log_id()
        self.embedder.process_documents(log_id)

    def run(self):
        raw = self.ingest()
        docs = self.process()
        self.embed()