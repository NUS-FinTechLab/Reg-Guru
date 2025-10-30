from abc import ABC, abstractmethod

class BasePipeline(ABC):
    """ Base class for all region-specific pipelines. """
    def __init__(self, test_mode):
        """
        Subclasses must accept test_mode, but they are not required to store it. They may use it only for initialization logic.
        """
        pass
    @abstractmethod
    def ingest(self) -> int:
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
        new_entries_num = self.ingest()
        if new_entries_num == 0:
            print("No documents required processing.")
        else:
            count = 1
            for minibatch in self.process():
                print("Embed batch ", count)
                self.embed(minibatch)
                count += 1