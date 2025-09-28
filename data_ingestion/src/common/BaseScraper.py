import psycopg2
from psycopg2 import extras
from abc import ABC, abstractmethod
from dotenv import load_dotenv
load_dotenv(override=True)

from .DBClient import DBClient

class BaseScraper(ABC):
    """Base class for all scrapers with database connection functionality."""
    """Input para"""
    
    def __init__(self, ds_name, ds_code, ds_description):
        """Initialize the scraper with data source insertion and database connection setup."""
        self.ds_code = ds_code
        self.ds_description = ds_description
        self.s3_obj = None
        self.db_client = DBClient()
        self.log_id = None
        self.ds_id = self._create_data_source(ds_name, ds_code, ds_description)

    def _create_data_source(self, name, code, description):
        self.db_client.connect()
        query = f"""SELECT id FROM ref.data_sources WHERE name = '{name}';"""
        result = self.db_client.execute(query)
        if result and result[0] and result[0][0] > 0:
            return result[0][0]
        else:
            query = """INSERT INTO ref.data_sources (name, code, description) VALUES (%s, %s, %s) RETURNING id;"""
            values = (name, code, description)
            try:
                ds_id = self.execute(query, values)
            except Exception as e:
                print(f"Error creating data source entry: {str(e)}")
                raise
            if not ds_id or not ds_id[0] or not ds_id[0][0]:
                raise Exception("Failed to create or retrieve data source ID")
        self.db_client.close()
        print("data_source", ds_id)
        return ds_id[0][0]
    
    def get_log_id(self):
        return self.log_id
    
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