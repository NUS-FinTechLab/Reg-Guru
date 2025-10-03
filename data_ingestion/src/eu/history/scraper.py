import os
import json
import feedparser
import requests
import pandas as pd
from dateutil import parser
from dotenv import load_dotenv
load_dotenv(override=True)

from common.BaseScraper import BaseScraper

HISTORY_CSV_KEY = "data_ingestion/raw/eu/eurlex-history/24_finance_search.csv"

class EUHistoryIngestor(BaseScraper):
    def __init__(self, ds_name, ds_code, ds_description):
        super().__init__(ds_name, ds_code, ds_description)
        self.history_csv_key = HISTORY_CSV_KEY
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.s3_obj = "data_ingestion/raw/eu/eurlex-feed"
        self.s3_obj_mtd = "data_ingestion/raw/eu/eurlex-feed-metadata"
        self.docs_to_insert = None
        return
    
    def parse(self):
        obj = self.s3_client.client.get_object(Bucket=self.bucket_name, Key=self.history_csv_key)
        entries = pd.read_csv(obj).sort_values(by='CELEX number', ascending=False)

    
if __name__ == "main":
    scraper = EUHistoryIngestor(
        ds_name='eurlex history',
        ds_code='eu',
        ds_description='European Union official publications and legal (historical data in searching for Eurovoc 24 Finance)'
    )
    scraper.parse()