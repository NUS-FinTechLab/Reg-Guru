import os
import requests
import pandas as pd
from tqdm import tqdm
from io import StringIO
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv(override=True)

from common.BaseScraper import BaseScraper

HISTORY_CSV_KEY = "data_ingestion/raw/eu/eurlex-history/24_finance_search.csv"
DEFAULT_DS_NAME = "eu_eurlex"

class EUHistoryIngestor(BaseScraper):
    def __init__(self, ds_name, ds_code, ds_description, test_mode):
        # Initialize data sources with 'history'
        super().__init__(ds_name, ds_code, ds_description, test_mode)
        # Change the ds details because raw data are ingested to the same feed pipeline tables
        self.ds_name = DEFAULT_DS_NAME if not test_mode else f"{DEFAULT_DS_NAME}_test"
        self.history_csv_key = HISTORY_CSV_KEY
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.s3_obj = "data_ingestion/raw/eu/eurlex-feed"
        self.s3_obj_mtd = "data_ingestion/raw/eu/eurlex-feed-metadata"
        self.docs_to_insert = None
        return
    
    def make_link(self, celex_number):
        return f"https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{celex_number}"
    
    def make_download_url(self, celex_number):
        return f"https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:{celex_number}"
    
    def keep_earliest_date(self, date_str):
        return min(date_str.split(', ')) if date_str else None


    def parse(self):
        obj = self.s3_client.client.get_object(Bucket=self.bucket_name, Key=self.history_csv_key)
        data = obj['Body'].read().decode("utf-8")
        entries = pd.read_csv(StringIO(data))
        if self.test_mode:
            return entries.iloc[10:12] # test
        else:
            return entries
        # entries = pd.read_csv(obj).sort_values(by='CELEX number', ascending=False)

    def find_latest_consolidated_version(self, celex_number):
        """
        Scrape the latest consolidated version date for a given CELEX number to see if there are updates.
        """
        url = self.make_link(celex_number)
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        main_content = soup.find('div', id='MainContent')
        cons_leg_versions = main_content.find('div', id='consLegVersions')
        latest_cons = cons_leg_versions.select_one("nav.consLegNav ul li a")
        latest_cons_date = datetime.strptime(latest_cons.text.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
        return {"celex_number": latest_cons['data-celex'].strip(), "link": self.make_link(latest_cons['data-celex'].strip()), "date": latest_cons_date}

    def log_into_database(self, entries):
        # Create feeds table if not exists
        self.db_client.connect()
        query = f"""CREATE TABLE IF NOT EXISTS bronze.feeds_{self.ds_name} (
            id SERIAL PRIMARY KEY,
            log_id INT NOT NULL REFERENCES logs.feeds(id) ON DELETE RESTRICT,
            title TEXT,
            summary TEXT,
            celex_number TEXT,
            link TEXT,
            download_url TEXT,
            uri_id TEXT,
            guidislink BOOLEAN,
            published TIMESTAMP,
            published_tz TIMESTAMPTZ,
            latest_consolidated TIMESTAMP,
            author TEXT,
            inserted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            flag SMALLINT NOT NULL DEFAULT 0 REFERENCES ref.review_status(id),
            remark TEXT
        );"""
        self.db_client.execute(query)
        self.docs_to_insert = entries

        # Logging starts
        query = """INSERT INTO logs.feeds (source_id, stage) VALUES (%s, %s) RETURNING id;"""
        self.log_id = self.db_client.execute(query, (self.ds_id, 0))[0][0]
        print(f"Log ID: {self.log_id}")

        # Insert entries
        query = f"""
            INSERT INTO bronze.feeds_{self.ds_name} (log_id, title, celex_number, link, download_url, published, published_tz, latest_consolidated, author, remark)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        for _, e in self.docs_to_insert.iterrows():
            if pd.notna(e['Latest consolidated version']):
                latest_cons = self.find_latest_consolidated_version(e['CELEX number'])
                values = (
                    self.log_id, 
                    e['Title'], 
                    e['CELEX number'], 
                    latest_cons['link'], 
                    self.make_download_url(latest_cons['celex_number']),
                    self.keep_earliest_date(e['Date of publication']),
                    self.keep_earliest_date(e['Date of publication']), 
                    latest_cons['date'],
                    e['Author'],
                    f"Consolidated Celex Number: {latest_cons['celex_number']}"
                )
            else:
                values = (
                    self.log_id, 
                    e['Title'], 
                    e['CELEX number'], 
                    self.make_link(e['CELEX number']), 
                    self.make_download_url(e['CELEX number']),
                    self.keep_earliest_date(e['Date of publication']),
                    self.keep_earliest_date(e['Date of publication']), 
                    None,
                    e['Author'],
                    None
                )
            try:
                self.db_client.execute(query, values)
            except Exception as exp:
                print(f"[{self.log_id}]", f"Error inserting {e['CELEX number']}:", exp)
                query = """INSERT INTO logs.feeds (source_id, remark, stage) VALUES (%s, %s, %s);"""
                self.db_client.execute(query, (self.ds_id, f"Error inserting {e['CELEX number']}:", 2))
                raise
        
        # Logging succeeds
        query = """INSERT INTO logs.feeds (source_id, stage) VALUES (%s, %s);"""
        self.db_client.execute(query, (self.ds_id, 1))
        
        # Print summary
        query = f"SELECT COUNT(id) FROM bronze.feeds_{self.ds_name} WHERE log_id = {self.log_id} AND flag = 0"
        new_entries_num = self.db_client.execute(query)

        print(f"{new_entries_num[0][0]} entries logged into bronze.feeds_{self.ds_name}.")
        self.db_client.close()
        return new_entries_num[0][0]
    
    def store_documents(self, log_id):
        self.db_client.connect()
        query = f"SELECT download_url, celex_number FROM bronze.feeds_{self.ds_name} WHERE log_id = {log_id} AND flag = 0"
        new_entries = self.db_client.execute(query)
        self.db_client.close()
        s3_folder = self.s3_obj + '/' + str(log_id)
        for entry in tqdm(new_entries, desc="Storing documents"):
            url = entry['download_url']
            response = requests.get(url)
            celex = entry['celex_number']
            file_obj_key = s3_folder + '/' + celex + ".html"  # sanitize filename
            self.s3_client.client.put_object(
                Bucket=self.bucket_name,
                Key=file_obj_key,
                Body=response.content,
                ContentType="text/html; charset=utf-8"
            )
        print(f"{len(new_entries)} documents uploaded to S3 {s3_folder}.")
        
        meta_obj_key = self.s3_obj_mtd + '/' + f"{log_id}.json"
        response = self.s3_client.client.list_objects_v2(Bucket=self.bucket_name, Prefix=self.s3_obj_mtd)
        # Check if metadata exists in s3
        if meta_obj_key in response: 
            print(f"Metadata {meta_obj_key} exists in {self.s3_obj_mtd}.")
        else:
            try:
                entries_list = self.docs_to_insert.to_json(orient="records")
                self.s3_client.client.put_object(
                        Bucket=self.bucket_name,
                        Key=meta_obj_key,
                        Body=entries_list.encode('utf-8'),
                        ContentType="application/json; charset=utf-8"
                    )
                print(f"Metadata {log_id}.json uploaded to S3 {self.s3_obj_mtd}.")
            except TypeError as e:
                print(f"docs_to_insert is None or not iterable: {e}")
                raise
            except Exception as e:
                print(e)
        return
    
    def get_log_id(self):
        return self.log_id
    
    def run(self):
        entries = self.parse()
        new_entries_num = self.log_into_database(entries)
        self.store_documents(self.log_id)
        return new_entries_num
    
if __name__ == "__main__":
    # scraper = EUHistoryIngestor(
    #     ds_name='eu_eurlex_test',
    #     ds_code='eu',
    #     ds_description='European Union official publications and legal (historical data in the Eurovoc 24 Finance search) (test)'
    # )
    scraper = EUHistoryIngestor()
    result = scraper.run()
    print(result)