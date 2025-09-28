from abc import ABC, abstractmethod

class IngestionPipeline(ABC):
    """ Base class for all region-specific pipelines. """

    @abstractmethod
    def ingest(self):
        """ Extract raw data and update database. Returns nothing. """
        pass

    @abstractmethod
    def process(self):
        """ Process raw data into cleaned texts and metadata. Generator of mini-batches. """
        pass

    @abstractmethod
    def embed(self, minibatch):
        """ Embed a mini-batch of documents into vector DB. """
        pass

    def run(self):
        self.ingest()
        for minibatch in self.process():
            self.embed(minibatch)