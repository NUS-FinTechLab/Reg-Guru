"""
One-time ingestor + processor for EU Historical Regulatory Documents
"""

import os
import json
import boto3
import requests
import pandas as pd
from tqdm import tqdm
from data_ingestion.src.pipelines.init_database import db_execute, db_insert_batch

class EUHistoricalDataProcessor:
    def __init__(self):
        self.ds_id = 3
        self.ds_description = 'eurlex - historical doc'
        self.log_id = None
        self.s3_obj = "data_ingestion/raw/eu/eurlex-feed"
        self.s3_obj_mtd = "data_ingestion/raw/eu/eurlex-feed-metadata"
        self.raw_meta_table = 'bronze.feeds_eu'
        self.clean_meta_table = 'silver.metadata'
        return
    
    def make_link(self, celex_number):
        return f"https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{celex_number}"
    
    def keep_earliest_date(self, date_str):
        return min(date_str.split(', ')) if date_str else None

    def log_db(self, entries):
        # Log logs - start
        query = """INSERT INTO logs.feeds (source_id, remark, stage) VALUES (%s, %s, %s) RETURNING id;"""
        self.log_id = db_execute(query, (self.ds_id, self.ds_description, 1))
        print(f"Log ID: {self.log_id[0][0]}")
        
        # Log entries
        query = """
                INSERT INTO bronze.feeds_eu (log_id, title, celex_number, link, published, published_tz, author)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
        values = [(self.log_id[0][0], e['Title'], e['CELEX number'], self.make_link(e['CELEX number']), self.keep_earliest_date(e['Date of publication']),self.keep_earliest_date(e['Date of publication']), e['Author']) for _, e in entries.iterrows()]
        db_insert_batch(query, values)
        
        # Log logs - success
        query = """INSERT INTO logs.feeds (source_id, remark, stage) VALUES (%s, %s, %s);"""
        db_execute(query, (self.ds_id, self.ds_description, 2))
        
        # Print summary
        query = f"SELECT COUNT(id) FROM bronze.feeds_eu WHERE log_id = {self.log_id[0][0]}"
        new_entries_num = db_execute(query)
        print(f"{new_entries_num[0][0]} entries logged into database.")
        return

    def store_documents(self, log_id, entries_list):
        query = f"SELECT link, celex_number FROM bronze.feeds_eu WHERE log_id = {log_id}"
        new_entries = db_execute(query)
        if len(new_entries) > 0:
            new_feed_folder = self.s3_obj + '/' + str(log_id)
            s3 = boto3.client(
                's3',
                aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY")
            )
            bucket_name = os.getenv("S3_BUCKET_NAME")
            
            for entry in tqdm(new_entries):
                url = entry['link']
                response = requests.get(url)
                celex = entry['celex_number']
                file_obj_key = new_feed_folder + '/' + celex + ".xml"  # sanitize filename
                s3.put_object(
                    Bucket=bucket_name,
                    Key=file_obj_key,
                    Body=response.content,
                    ContentType="application/xml; charset=utf-8"
                )
            print(f"{len(new_entries)} documents uploaded to S3 {new_feed_folder}.")
            
            entries_list = entries_list.to_dict(orient='records')
            meta_obj_key = self.s3_obj_mtd + '/' + f"{log_id}.json"
            s3 = boto3.client(
                    's3',
                    aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY")
                )
            bucket_name = os.getenv("S3_BUCKET_NAME")
            s3.put_object(
                    Bucket=bucket_name,
                    Key=meta_obj_key,
                    Body=json.dumps(entries_list).encode('utf-8'),
                    ContentType="application/json; charset=utf-8"
                )
            print(f"metadata uploaded to S3 {self.s3_obj_mtd}.")
        else:
            print("No new documents from this feed.")
        
        return
        
    def clean_metadata(self, log_id): 
        """Prepare ready-to-use metadata in Silver"""
        query = f"SELECT source_id FROM logs.feeds WHERE id = {log_id}"
        source_id = db_execute(query)
        source_id = source_id[0][0]
        query = f"SELECT * FROM {self.raw_meta_table} WHERE log_id = {log_id}"
        new_entries = db_execute(query)
        meta = pd.DataFrame(new_entries, columns=new_entries[0].keys() if new_entries else [])
        for _, row in meta.iterrows():
            query = """
                INSERT INTO silver.metadata (id, source_id, log_id, title, link, published, author, unique_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (row['id'], source_id, log_id, row['title'], row['link'], row['published'], row['author'], row['celex_number'])
            db_execute(query, values)
        print("Metadata cleaned and saved to silver.metadata")
        return

    def process_documents(self):
        # Read historical data from local CSV
        current_dir = os.path.dirname(os.path.abspath(__file__))
        history_path = os.path.join(current_dir, '..', '..', 'raw', 'eu', 'eurlex-feed', '24_finance_search.csv')
        entries = pd.read_csv(history_path).sort_values(by='CELEX number', ascending=False)
        self.log_db(entries)
        self.store_documents(self.log_id[0][0], entries)
        self.clean_metadata(self.log_id[0][0])
        return

if __name__ == "__main__":
    processor = EUHistoricalDataProcessor()
    processor.process_documents()
