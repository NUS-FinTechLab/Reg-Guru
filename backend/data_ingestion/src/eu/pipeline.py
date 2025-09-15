from common.pipeline_base import IngestionPipeline
from eu.EUFeedIngestor import EUFeedIngestor

class EUFeedPipeline(IngestionPipeline):
    """EU pipeline implementation."""

    def __init__(self):
        super().__init__()
        self.ingestor = EUFeedIngestor("https://eur-lex.europa.eu/EN/display-feed.rss?myRssId=zqe48ppy80IwdPmk3HJVPsD4fM281XNaoMTLQ6ifL58%3D")
        

    def ingest(self):
        """Download or read raw data (return list of file paths or bytes)."""
        self.ingestor.run()
        return

    def process(self, raw_data):
        """Convert raw data into structured docs (list of dicts)."""
        pass

    def embed(self, docs):
        """Embed documents into Chroma or other vector DB."""
        pass

    def run(self):
        raw = self.ingest()
        docs = self.process(raw)
        self.embed(docs)