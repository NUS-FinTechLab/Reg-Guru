"""
Feed ingestor for EUR-Lex RSS Feed
"""

import os
import json
import feedparser
import boto3
import requests
from dateutil import parser
from datetime import datetime, timezone
from common.database import db_execute
from dotenv import load_dotenv
load_dotenv(override=True)

class EUFeedIngestor:
    def __init__(self, rss_url):
        self.rss_url = rss_url
        self.s3_obj = "data_ingestion/raw/eu/eurlex-feed"
        self.ds_id = 2
        self.ds_description = 'eurlex - test feed'
        self.feed = None
        self.log_id = None
        return

    def parse(self):
        self.feed = feedparser.parse(self.rss_url)
        print(f"Feed parsed with {len(self.feed.entries)} entries.")
        return
    
    def log_db(self):
        query = """SELECT published, uri_id FROM bronze.feeds_test_eu ORDER BY published DESC LIMIT 1"""
        result = db_execute(query)
        if result:
            latest_date = result[0][0]
            if not latest_date.tzinfo:
                # assume DB value is in local timezone, convert to UTC
                latest_date = latest_date.replace(tzinfo=timezone.utc)
            else:
                # convert aware datetime to UTC
                latest_date = latest_date.astimezone(timezone.utc)
        else:
            latest_date = None # No previous data

        query = """INSERT INTO logs.feeds (source_id, remark, stage) VALUES (%s, %s, %s) RETURNING id;"""
        self.log_id = db_execute(query, (self.ds_id, self.ds_description, 1))

        for entry in self.feed.entries: # feed entries are desc ordered by time
            if latest_date and parser.parse(entry.published).astimezone(timezone.utc) <= latest_date:
                break
            query = """
                INSERT INTO bronze.feeds_test_eu (log_id, title, summary, link, uri_id, guidislink, published, author, flag, remark)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                self.log_id[0][0], entry.title, entry.summary, entry.link, entry.id, entry.guidislink,
                parser.parse(entry.published).astimezone(timezone.utc),
                entry.author, 0, None
            )
            try:
                db_execute(query, values)
            except Exception as e:
                print(f"[{self.log_id[0][0]}] Error inserting entry {entry.id}: {e}")
                query = """INSERT INTO logs.feeds (source_id, remark, stage) VALUES (%s, %s, %s);"""
                db_execute(query, (self.ds_id, self.ds_description, 3))
                raise

        query = """INSERT INTO logs.feeds (source_id, remark, stage) VALUES (%s, %s, %s);"""
        db_execute(query, (self.ds_id, self.ds_description, 2))
        query = f"SELECT COUNT(id) FROM bronze.feeds_test_eu WHERE log_id = {self.log_id[0][0]}"
        new_entries_num = db_execute(query)
        print(f"{new_entries_num[0][0]} entries logged into database.")
        return
    
    def store_documents(self):
        query = f"SELECT link, title FROM bronze.feeds_test_eu WHERE log_id = {self.log_id[0][0]}"
        new_entries = db_execute(query)
        if len(new_entries) > 0:
            new_feed_folder = self.s3_obj + '/' + str(self.log_id[0][0])
            s3 = boto3.client(
                's3',
                aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY")
            )
            bucket_name = os.getenv("S3_BUCKET_NAME")
            
            for entry in new_entries:
                url = entry['link']
                response = requests.get(url)
                celex = entry['title'].split(":")[1].strip()
                file_obj_key = new_feed_folder + '/' + celex + ".xml"  # sanitize filename
                s3.put_object(
                    Bucket=bucket_name,
                    Key=file_obj_key,
                    Body=response.content,
                    ContentType="application/xml; charset=utf-8"
                )
            print(f"{len(new_entries)} documents uploaded to S3 {new_feed_folder}.")

            entries_list = [dict(entry) for entry in self.feed.entries]
            meta_obj_key = new_feed_folder + '/' + "metadata.json"
            s3.put_object(
                    Bucket=bucket_name,
                    Key=meta_obj_key,
                    Body=json.dumps(entries_list).encode('utf-8'),
                    ContentType="application/json; charset=utf-8"
                )
            print(f"metadata.json uploaded to S3 {new_feed_folder}.")
        else:
            print("No new documents from this feed.")
        return
    
    def get_log_id(self):
        return self.log_id
    
    def run(self):
        self.parse()
        self.log_db()
        self.store_documents()
        return