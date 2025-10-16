import re
from abc import ABC, abstractmethod
from typing import List
from .DBClient import DBClient
from .S3Client import S3Client

class BaseProcessor(ABC):
    def __init__(self, ds_code, batch_size):
        self.ds_code = ds_code
        self.batch_size = batch_size
        self.db_client = DBClient()
        self.s3_client = S3Client()
        self.s3_obj = None
        self._initialise_clean_metadata_table()
    
    def _initialise_clean_metadata_table(self):
        self.db_client.connect()
        query = """CREATE TABLE IF NOT EXISTS silver.metadata (
            id INT NOT NULL,
            source_id INT NOT NULL,
            log_id INT NOT NULL REFERENCES logs.feeds(id) ON DELETE RESTRICT,
            title TEXT,
            weblink TEXT,
            download_url TEXT,
            published_date TIMESTAMP,
            valid_date TIMESTAMP,
            author TEXT,
            unique_id TEXT NOT NULL,
            inserted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            flag SMALLINT NOT NULL DEFAULT 0,
            CONSTRAINT pk_silver_metadata PRIMARY KEY (id, source_id),
            CONSTRAINT fk_log_id FOREIGN KEY (log_id) REFERENCES logs.feeds(id) ON DELETE RESTRICT,
            CONSTRAINT fk_flag FOREIGN KEY (flag) REFERENCES ref.review_status(id)
            );"""
        self.db_client.execute(query)
        self.db_client.close()
        
        return
    
    def check_if_metadata_cleaned(self, log_id):
        self.db_client.connect()
        query = "SELECT COUNT(id) FROM silver.metadata WHERE log_id = %s LIMIT 1"
        result = self.db_client.execute(query, (log_id,))[0][0]
        self.db_client.close()
        return result > 0
    
    def clean_texts(self, texts: List[str]) -> str:
        """ A common method to clean and normalize text """
        cleaned_texts = []
        for text in texts:
            text = text.replace("\xa0", " ")
            text = re.sub(r"[ \t]+", " ", text)
            text = re.sub(r"\n+", "\n", text)
            text = text.strip()
            if text:
                cleaned_texts.append(text)
        return cleaned_texts
    
    @abstractmethod
    def clean_metadata(self, log_id):
        pass

    @abstractmethod
    def extract_texts(self, key) -> List[str]:
        pass

    @abstractmethod
    def run(self, log_id):
        pass
