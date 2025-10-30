from abc import ABC, abstractmethod
from dotenv import load_dotenv

load_dotenv(override=True)

from .DBClient import DBClient
from .S3Client import S3Client


class BaseScraper(ABC):
    """Base class for all scrapers with optional database integration."""

    def __init__(self, ds_name: str=None, ds_code: str=None, ds_description: str=None, test_mode: bool=False) -> None:
        """Initialize the scraper; data source metadata is optional for simple scrapers."""
        self.ds_name = ds_name
        self.ds_code = ds_code # The ref.data_sources.code column is VARCHAR(5) usually the first few characters in ds_name representing region.
        self.ds_description = ds_description
        self.db_client = DBClient()
        self.s3_client = S3Client()
        self.ds_id = None
        if all([ds_name, ds_code, ds_description]):
            self.ds_id = self._create_data_source(ds_name, ds_code, ds_description)
        else:
            raise ValueError("Data source name, code, and description must be provided.")
        self.metadata_table = 'silver.metadata' if not test_mode else 'silver.metadata_test'
        self.test_mode = test_mode
        self.log_id = None
        self.s3_obj = None

    def _create_data_source(self, name, code, description):
        """
        Insert a data source if it doesn't exist. 
        Name is unique in ref.data_sources.
        """
        self.db_client.connect()
        query = "SELECT id FROM ref.data_sources WHERE name = %s;"
        result = self.db_client.execute(query, (name,))
        if result and result[0] and result[0][0] > 0:
            self.db_client.close()
            return result[0][0]
        else:
            query = """INSERT INTO ref.data_sources (name, code, description) VALUES (%s, %s, %s) RETURNING id;"""
            values = (name, code, description)
            try:
                ds_id = self.db_client.execute(query, values)
            except Exception as e:
                print(f"Error creating data source entry: {str(e)}")
                raise
            if not ds_id or not ds_id[0] or not ds_id[0][0]:
                raise Exception("Failed to create or retrieve data source ID")
        self.db_client.close()
        return ds_id[0][0]

    def get_log_id(self):
        return self.log_id
    
    def get_data_source_name(self):
        return self.ds_name
    
    def get_data_source_code(self):
        return self.ds_code

    def close_connection(self):
        """Helper to close the associated DB connection if one is open."""
        self.db_client.close()

    @abstractmethod
    def log_into_database(self, **kwargs) -> int:
        """
        Abstract method for logging data into the database.
        Each scraper implementation should define their own logging logic.
        """
        pass

    @abstractmethod
    def store_documents(self, log_id, **kwargs):
        """
        Abstract method for storing documents (e.g., to S3).
        Each scraper implementation can override this if needed.
        """
        pass

    @abstractmethod
    def run(self, **kwargs) -> int:
        """
        Abstract method for scraping functionality.
        Each scraper implementation should define their own scraping logic.
        """
        pass
