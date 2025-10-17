import os
import requests
import pandas as pd
from tqdm import tqdm
from io import StringIO
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
    
    def make_link(self, celex_number):
        return f"https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{celex_number}"
    
    def keep_earliest_date(self, date_str):
        return min(date_str.split(', ')) if date_str else None


    def parse(self):
        obj = self.s3_client.client.get_object(Bucket=self.bucket_name, Key=self.history_csv_key)
        data = obj['Body'].read().decode("utf-8")
        entries = pd.read_csv(StringIO(data))
        return entries #test
        # entries = pd.read_csv(obj).sort_values(by='CELEX number', ascending=False)

    def log_into_database(self, entries):
        # Create feeds table if not exists
        self.db_client.connect()
        query = f"""CREATE TABLE IF NOT EXISTS bronze.feeds_{self.ds_code} (
            id SERIAL PRIMARY KEY,
            log_id INT NOT NULL REFERENCES logs.feeds(id) ON DELETE RESTRICT,
            title TEXT,
            summary TEXT,
            celex_number TEXT,
            link TEXT,
            uri_id TEXT,
            guidislink BOOLEAN,
            published TIMESTAMP,
            published_tz TIMESTAMPTZ,
            author TEXT,
            inserted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            flag SMALLINT NOT NULL DEFAULT 0 REFERENCES ref.review_status(id),
            remark TEXT
        );"""
        self.db_client.execute(query)
        self.docs_to_insert = entries

        # Logging starts
        query = """INSERT INTO logs.feeds (source_id, remark, stage) VALUES (%s, %s, %s) RETURNING id;"""
        self.log_id = self.db_client.execute(query, (self.ds_id, self.ds_description, 0))[0][0]
        print(f"Log ID: {self.log_id}")

        # Insert entries
        query = f"""
            INSERT INTO bronze.feeds_{self.ds_code} (log_id, title, celex_number, link, published, published_tz, author)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        for _, e in self.docs_to_insert.iterrows(): # feed entries are desc ordered by time
            values = (
                self.log_id, e['Title'], e['CELEX number'], self.make_link(e['CELEX number']), self.keep_earliest_date(e['Date of publication']),self.keep_earliest_date(e['Date of publication']), e['Author']
            )
            try:
                self.db_client.execute(query, values)
            except Exception as e:
                print(f"[{self.log_id}] Error inserting entry {e['CELEX number']}: {e}")
                query = """INSERT INTO logs.feeds (source_id, remark, stage) VALUES (%s, %s, %s);"""
                self.db_client.execute(query, (self.ds_id, self.ds_description, 2))
                raise
        
        # Logging succeeds
        query = """INSERT INTO logs.feeds (source_id, remark, stage) VALUES (%s, %s, %s);"""
        self.db_client.execute(query, (self.ds_id, self.ds_description, 1))
        
        # Print summary
        query = f"SELECT COUNT(id) FROM bronze.feeds_{self.ds_code} WHERE log_id = {self.log_id}"
        new_entries_num = self.db_client.execute(query)

        print(f"{new_entries_num[0][0]} entries logged into bronze.feeds_{self.ds_code}.")
        self.db_client.close()
        return new_entries_num[0][0]
    
    def store_documents(self, log_id):
        self.db_client.connect()
        query = f"SELECT link, celex_number FROM bronze.feeds_{self.ds_code} WHERE log_id = {log_id}"
        new_entries = self.db_client.execute(query)
        self.db_client.close()
        s3_folder = self.s3_obj + '/' + str(log_id)
        for entry in tqdm(new_entries, desc="Storing documents"):
            url = entry['link']
            response = requests.get(url)
            celex = entry['celex_number']
            file_obj_key = s3_folder + '/' + celex + ".xml"  # sanitize filename
            self.s3_client.client.put_object(
                Bucket=self.bucket_name,
                Key=file_obj_key,
                Body=response.content,
                ContentType="application/xml; charset=utf-8"
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
    
    def run(self):
        entries = self.parse()
        new_entries_num = self.log_into_database(entries)
        self.store_documents(self.log_id)
        return new_entries_num
    
if __name__ == "__main__":
    scraper = EUHistoryIngestor(
        ds_name='eurlex history (test)',
        ds_code='te',
        ds_description='European Union official publications and legal (historical data in the Eurovoc 24 Finance search) (test)'
    )
    result = scraper.run()
    