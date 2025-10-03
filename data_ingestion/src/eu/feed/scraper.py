"""
Feed ingestor for EUR-Lex RSS Feed
"""

import os
import json
import feedparser
import requests
from dateutil import parser
from dotenv import load_dotenv
load_dotenv(override=True)

from common.BaseScraper import BaseScraper

RSS_URL = "https://eur-lex.europa.eu/EN/display-feed.rss?myRssId=zqe48ppy80IwdPmk3XxQMlkGOfbi%2BE8KLQfclbDnbig%3D"

class EUFeedIngestor(BaseScraper):
    def __init__(self, ds_name, ds_code, ds_description):
        super().__init__(ds_name, ds_code, ds_description)
        self.rss_url = RSS_URL
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.s3_obj = "data_ingestion/raw/eu/eurlex-feed"
        self.s3_obj_mtd = "data_ingestion/raw/eu/eurlex-feed-metadata"
        self.docs_to_insert = None
        return

    def parse(self):
        documents = feedparser.parse(self.rss_url)
        if documents.status != 200:
            raise Exception(f"Abnormal parsing: {documents.status}")
        entries = sorted(documents.entries, key=lambda x: parser.parse(x['published']), reverse=True)[10:12]
        print(f"Feed parsed with {len(entries)} entries.")
        return entries
    
    def log_into_database(self, entries):
        # Skip if no documents from feed to insert
        if len(entries) == 0:
            print("No data from feed to insert.")
            return 0
        
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

        # Retrieve existing documents to avoid duplicates
        query = f"""SELECT published_tz FROM bronze.feeds_{self.ds_code} ORDER BY published_tz DESC LIMIT 1"""
        result = self.db_client.execute(query)
        if len(result) > 0:
            latest_date = result[0][0]
            self.docs_to_insert = [entry for entry in entries if parser.parse(entry.published) > latest_date]
        else:
            print("No existing documents found, inserting all scraped documents.")
            self.docs_to_insert = entries

        print(len(self.docs_to_insert))
        if len(self.docs_to_insert) == 0:
            print("No new or updated documents to insert.")
            self.db_client.close()
            return 0
        else:
            # Logging starts
            query = """INSERT INTO logs.feeds (source_id, remark, stage) VALUES (%s, %s, %s) RETURNING id;"""
            self.log_id = self.db_client.execute(query, (self.ds_id, self.ds_description, 0))[0][0]
            print(f"Log ID: {self.log_id}")

            # Insert entries
            query = f"""
                INSERT INTO bronze.feeds_{self.ds_code} (log_id, title, summary, link, uri_id, guidislink, published, published_tz, author)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            for entry in self.docs_to_insert: # feed entries are desc ordered by time
                values = (
                    self.log_id, entry.title, entry.summary, entry.link, entry.id, entry.guidislink,
                    parser.parse(entry.published).date(), parser.parse(entry.published), entry.author
                )
                try:
                    self.db_client.execute(query, values)
                except Exception as e:
                    print(f"[{self.log_id}] Error inserting entry {entry.id}: {e}")
                    query = """INSERT INTO logs.feeds (source_id, remark, stage) VALUES (%s, %s, %s);"""
                    self.db_client.execute(query, (self.ds_id, self.ds_description, 2))
                    raise
            
            # Logging succeeds
            query = """INSERT INTO logs.feeds (source_id, remark, stage) VALUES (%s, %s, %s);"""
            self.db_client.execute(query, (self.ds_id, self.ds_description, 1))
            
            # Print summary
            query = f"SELECT COUNT(id) FROM bronze.feeds_{self.ds_code} WHERE log_id = {self.log_id}"
            new_entries_num = self.db_client.execute(query)
    
            print(f"{new_entries_num[0][0]} entries logged into database.")
            self.db_client.close()
            return new_entries_num[0][0]
    
    def store_documents(self, log_id):
        self.db_client.connect()
        query = f"SELECT link, title FROM bronze.feeds_{self.ds_code} WHERE log_id = {log_id}"
        new_entries = self.db_client.execute(query)
        self.db_client.close()
        # If there are new documents to store
        if len(new_entries) > 0:
            new_feed_folder = self.s3_obj + '/' + str(log_id)
            
            for entry in new_entries:
                url = entry['link']
                response = requests.get(url)
                celex = entry['title'].split(':')[1].strip()
                file_obj_key = new_feed_folder + '/' + celex + ".xml"  # sanitize filename
                self.s3_client.client.put_object(
                    Bucket=self.bucket_name,
                    Key=file_obj_key,
                    Body=response.content,
                    ContentType="application/xml; charset=utf-8"
                )
            print(f"{len(new_entries)} documents uploaded to S3 {new_feed_folder}.")
            
            meta_obj_key = self.s3_obj_mtd + '/' + f"{log_id}.json"
            response = self.s3_client.client.list_objects_v2(Bucket=self.bucket_name, Prefix=self.s3_obj_mtd)
            # Check if metadata exists in s3
            if meta_obj_key in response: 
                print(f"Metadata {meta_obj_key} exists in {self.s3_obj_mtd}.")
            else:
                try:
                    entries_list = [dict(entry) for entry in self.docs_to_insert]
                    self.s3_client.client.put_object(
                            Bucket=self.bucket_name,
                            Key=meta_obj_key,
                            Body=json.dumps(entries_list).encode('utf-8'),
                            ContentType="application/json; charset=utf-8"
                        )
                    print(f"Metadata {log_id}.json uploaded to S3 {self.s3_obj_mtd}.")
                except TypeError as e:
                    print(f"docs_to_insert is None or not iterable: {e}")
                    raise
                except Exception as e:
                    print(e)
        else:
            print("No new documents from this feed to store.")
        return
    
    def get_log_id(self):
        return self.log_id
    
    def run(self):
        entries = self.parse()
        new_entries_num = self.log_into_database(entries)
        self.store_documents(self.log_id)
        return new_entries_num
    
if __name__ == "__main__":
    ingestor = EUFeedIngestor(
        ds_name="eurlex feed (test)",
        ds_code="te",
        ds_description="European Union official publications and legal (test)"
    )
    ingestor.run()
