from abc import ABC, abstractmethod

class IngestionPipeline(ABC):
    """Base class for all region-specific pipelines."""

    @abstractmethod
    def ingest(self):
        """Download or read raw data (return list of file paths or bytes)."""
        pass

    @abstractmethod
    def process(self, raw_data):
        """Convert raw data into structured docs (list of dicts)."""
        pass

    @abstractmethod
    def embed(self, docs):
        """Embed documents into Chroma or other vector DB."""
        pass

    def run(self):
        raw = self.ingest()
        docs = self.process(raw)
        self.embed(docs)
