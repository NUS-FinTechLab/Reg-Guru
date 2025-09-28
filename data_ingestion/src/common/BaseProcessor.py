import re
from abc import ABC, abstractmethod
from typing import List
from .DBClient import DBClient
from .S3Client import S3Client

class BaseProcessor(ABC):
    def __init__(self, batch_size):
        self.raw_meta_table = None
        self.clean_meta_table = None
        self.s3_key_prefix = None
        self.db_client = DBClient()
        self.s3_client = S3Client()
        self.batch_size = batch_size

    def clean_texts(self, texts: List[str]) -> List[str]:
        """ A common method to clean and normalize texts """
        cleaned_texts = []
        for text in texts:
            text = text.replace("\xa0", " ")
            text = re.sub(r"[ \t]+", " ", text)
            text = re.sub(r"\n+", "\n", text)
            text = text.strip()
            if text:
                cleaned_texts.append(text)
        return '\n'.join(cleaned_texts)
    
    @abstractmethod
    def clean_metadata(self, log_id):
        pass

    @abstractmethod
    def extract_texts(self, key) -> List[str]:
        pass

    @abstractmethod
    def run(self, log_id):
        pass
