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
        self.embedder = EUFeedEmbedder()
        

    def ingest(self):
        """Download or read raw data (return list of file paths or bytes)."""
        self.ingestor.run()
        return

    def process(self):
        """Process raw data wherever necessary."""
        log_id = self.ingestor.get_log_id()
        self.processor(log_id)
        return

    def embed(self, docs):
        """Embed documents into Chroma or other vector DB."""
        pass

    def run(self):
        raw = self.ingest()
        docs = self.process(raw)
        self.embed(docs)