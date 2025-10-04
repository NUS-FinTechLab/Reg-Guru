from abc import ABC, abstractmethod
from dotenv import load_dotenv

load_dotenv(override=True)

from .DBClient import DBClient
from .S3Client import S3Client


class BaseScraper(ABC):
    """Base class for all scrapers with optional database integration."""

    def __init__(self, ds_name=None, ds_code=None, ds_description=None):
        """Initialize the scraper; data source metadata is optional for simple scrapers."""
        self.ds_code = ds_code
        self.ds_description = ds_description
        self.db_client = DBClient()
        self.s3_client = S3Client()
        self.ds_id = None

        if all([ds_name, ds_code, ds_description]):
            self.ds_id = self._create_data_source(ds_name, ds_code, ds_description)
        self.log_id = None
        self.s3_obj = None

    def _create_data_source(self, name, code, description):
        """Insert a data source if it doesn't exist"""
        self.db_client.connect()
        query = f"""SELECT id FROM ref.data_sources WHERE name = '{name}';"""
        result = self.db_client.execute(query)
        if result and result[0] and result[0][0] > 0:
            self.db_client.close()
            print(f"Existing data source:", result[0][0])
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
        print("Insert data source: ", ds_id[0][0])
        return ds_id[0][0]

    def get_log_id(self):
        return self.log_id

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
