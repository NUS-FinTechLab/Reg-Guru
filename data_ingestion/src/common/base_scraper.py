import os
import psycopg2
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from .helper import feed_exists_pg

# Load environment variables
load_dotenv()

class BaseScraper(ABC):
    """Base class for all scrapers with database connection functionality."""
    
    def __init__(self):
        """Initialize the scraper with database connection setup."""
        self.db_conn = None
        self._setup_database_connection()
    
    def _setup_database_connection(self):
        """Set up database connection using environment variables"""
        try:
            self.db_conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                dbname=os.getenv("DB_NAME")
            )
            print(f"Connected to PostgreSQL database for duplicate checking")
        except Exception as e:
            print(f"Warning: Could not connect to database: {str(e)}")
            print("Proceeding without duplicate filtering...")
    
    def _is_document_processed(self, url, title, region='us'):
        """Check if document already exists in database
        
        Args:
            url: The document URL to check
            title: The document title to check
            region: The region code (us, sg, eu) to determine which feeds table to check
            
        Returns:
            bool: True if document exists, False otherwise
        """
        if not self.db_conn:
            return False
        try:
            return feed_exists_pg(self.db_conn, url, title, region)
        except Exception as e:
            print(f"Warning: Error checking database: {str(e)}")
            return False
    
    def close_connection(self):
        """Close database connection"""
        if self.db_conn:
            try:
                self.db_conn.close()
                print("Database connection closed")
            except Exception as e:
                print(f"Error closing database connection: {str(e)}")
    
    @abstractmethod
    def scrape(self, **kwargs):
        """
        Abstract method for scraping functionality.
        Each scraper implementation should define their own scraping logic.
        """
        pass