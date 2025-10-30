"""
Feed ingestor for EUR-Lex RSS Feed
"""

import os
import json
import feedparser
import requests
import pandas as pd
from tqdm import tqdm
from dateutil import parser
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv(override=True)

from common.BaseScraper import BaseScraper

RSS_URL = "https://eur-lex.europa.eu/EN/display-feed.rss?myRssId=zqe48ppy80IwdPmk3XxQMlkGOfbi%2BE8KLQfclbDnbig%3D"

class EUFeedIngestor(BaseScraper):
    def __init__(self, ds_name, ds_code, ds_description, test_mode):
        super().__init__(ds_name, ds_code, ds_description, test_mode)
        self.rss_url = RSS_URL
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.s3_obj = "data_ingestion/raw/eu/eurlex-feed"
        self.s3_obj_mtd = "data_ingestion/raw/eu/eurlex-feed-metadata"
        self.new_records = None
        return

    def parse(self):
        documents = feedparser.parse(self.rss_url)
        if documents.status != 200:
            raise Exception(f"Abnormal parsing: {documents.status}")
        entries = sorted(documents.entries, key=lambda x: parser.parse(x['published']), reverse=True)
        print(f"Feed parsed with {len(entries)} entries.")
        if self.test_mode:
            return entries[14:17] # test
        else:
            return entries
    
    def make_link(self, celex_number):
        return f"https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{celex_number}"
    
    def make_download_url(self, celex_number):
        return f"https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:{celex_number}"

    def find_latest_consolidated_version(self, celex_number):
        """
        Scrape the latest consolidated version for a given CELEX number to see if there are updates.
        """
        url = self.make_link(celex_number)
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        main_content = soup.find('div', id='MainContent')
        eurlex_content = main_content.find('div', class_='EurlexContent')
        force_indicator = eurlex_content.find('p', class_='forceIndicator')
        if force_indicator is not None and force_indicator.text.strip() != 'In force':
            # There are consolidated versions
            cons_leg_versions = main_content.find('div', id='consLegVersions')
            latest_cons = cons_leg_versions.select_one("nav.consLegNav ul li a")
            latest_cons_date = datetime.strptime(latest_cons.text.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
            return {"celex_number": latest_cons['data-celex'].strip(), "link": self.make_link(latest_cons['data-celex'].strip()), "date": latest_cons_date}
        else:
            return None
    
    def insert_start_log(self):
        if self.log_id is None:
            query = """INSERT INTO logs.feeds (source_id, remark, stage) VALUES (%s, %s, %s) RETURNING id;"""
            self.log_id = self.db_client.execute(query, (self.ds_id, self.ds_description, 0))[0][0]
            print(f"Log ID: {self.log_id}")
        return
        
    def insert_documents(self):
        if len(self.new_records) == 0:
            print("No new documents to insert.")
            return 0
        else:
            self.insert_start_log()
            print(f"{len(self.new_records)} new documents to insert.")
            # Insert entries
            query = f"""
                INSERT INTO bronze.feeds_{self.ds_name} (log_id, title, celex_number, summary, link, download_url, uri_id, guidislink, published, published_tz, latest_consolidated, author, remark)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            for entry in self.new_records: # feed entries are desc ordered by time
                celex_number = entry.title.split(':')[1].strip()
                title = entry.title.split(':')[2].strip()
                latest_cons = self.find_latest_consolidated_version(celex_number)
                if latest_cons is not None:
                    values = (
                        self.log_id,
                        title,
                        celex_number,
                        entry.summary,
                        self.make_link(latest_cons['celex_number']),
                        self.make_download_url(latest_cons['celex_number']),
                        entry.id,
                        entry.guidislink,
                        parser.parse(entry.published).date(),
                        parser.parse(entry.published),
                        latest_cons['date'],
                        entry.author,
                        f"Consolidated Celex Number: {latest_cons['celex_number']}"
                    )
                else:
                    values = (
                        self.log_id,
                        title,
                        celex_number,
                        entry.summary,
                        self.make_link(celex_number),
                        self.make_download_url(celex_number),
                        entry.id,
                        entry.guidislink,
                        parser.parse(entry.published).date(),
                        parser.parse(entry.published),
                        None,
                        entry.author,
                        None
                    )
                try:
                    self.db_client.execute(query, values)
                except Exception as e:
                    print(f"[{self.log_id}] Error inserting entry {celex_number}: {e}")
                    # Logging fails
                    query = """INSERT INTO logs.feeds (source_id, remark, stage) VALUES (%s, %s, %s);"""
                    self.db_client.execute(query, (self.ds_id, "Failed in inserting new documents", 2))
                    self.db_client.close()
                    raise
            return len(self.new_records)

    def check_update_all_documents(self, records):
        """
        ref.review.status.flag = 3: Obsolete
        """
        if len(records) == 0:
            print("No existing documents to check updates.")
            return 0
        else:
            print(f"{len(records)} existing documents to check updates.")
            query_update_bronze = f"""UPDATE bronze.feeds_{self.ds_name} SET flag = 3 WHERE celex_number = %s AND flag = 0;"""
            query_update_silver = f"""UPDATE {self.metadata_table} SET flag = 3 WHERE celex_number = %s AND flag = 0;"""
            query_insert = f"""
                    INSERT INTO bronze.feeds_{self.ds_name} (log_id, title, celex_number, summary, link, download_url, uri_id, guidislink, published, published_tz, latest_consolidated, author, remark)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            update_count = 0
            for e in tqdm(records, desc="Checking new consolidated versions"):
                record_cons_date = e['latest_consolidated'].strftime("%Y-%m-%d") if pd.notna(e['latest_consolidated']) else None
                latest_cons = self.find_latest_consolidated_version(e['celex_number'])
                if latest_cons is not None and (record_cons_date is None or latest_cons['date'] > record_cons_date):
                    # There is new consolidated version
                    try:
                        self.insert_start_log()
                        self.db_client.execute(query_update_bronze, (e['celex_number'],))
                        self.db_client.execute(query_update_silver, (e['celex_number'],))
                        values_insert = (
                            self.log_id,
                            e['title'],
                            e['celex_number'],
                            e['summary'],
                            self.make_link(latest_cons['celex_number']),
                            self.make_download_url(latest_cons['celex_number']),
                            e['uri_id'],
                            e['guidislink'],
                            e['published'],
                            e['published_tz'],
                            latest_cons['date'],
                            e['author'],
                            f"Consolidated Celex Number: {latest_cons['celex_number']}"
                        )
                        self.db_client.execute(query_insert, values_insert)
                        update_count += 1
                    except Exception as exp:
                        print(f"[{self.log_id}] Error updating entry {e['celex_number']}: {exp}")
                        # Logging fails
                        query = """INSERT INTO logs.feeds (source_id, remark, stage) VALUES (%s, %s, %s);"""
                        self.db_client.execute(query, (self.ds_id, "Failed in updating new documents", 2))
                        self.db_client.close()
                        raise
            return update_count
            
    def log_into_database(self, entries):
        """
        If no logging is required, log_id is None, returning 0.
        If logging id required, log_id is not None, returning num > 0.
        """
        # Skip if no documents from feed to insert
        if len(entries) == 0:
            print("No data from feed to insert.")
            return 0
        
        # Ensure feeds table exists by running history pipeline first
        self.db_client.connect()
        
        #-------- Add new entries --------#
        # Retrieve the latest published date in database and compare to avoid duplicates
        query = f"""SELECT published_tz FROM bronze.feeds_{self.ds_name} WHERE flag = 0 ORDER BY published_tz DESC LIMIT 1"""
        result = self.db_client.execute(query)
        if len(result) > 0:
            latest_date = result[0][0]
            self.new_records = [entry for entry in entries if parser.parse(entry.published) > latest_date]
        else:
            self.new_records = entries
        insert_count = self.insert_documents()
        
        #-------- Update entries --------#
        # Retrieve previous documents to check for updates
        if self.log_id is None:
            query = f"""SELECT * FROM bronze.feeds_{self.ds_name} WHERE flag = 0"""
        else:
            query = f"""SELECT * FROM bronze.feeds_{self.ds_name} WHERE log_id < {self.log_id} AND flag = 0"""
        records = self.db_client.execute(query)
        records = [dict(row) for row in records]
        update_count = self.check_update_all_documents(records)

        if self.log_id is None:
            # No logging created
            self.db_client.close()
            print(f"Insert {insert_count} records; update {update_count} records.")
            print(f"No entries logged into bronze.feeds_{self.ds_name}.")
            return 0
        else:
            # Logging succeeds
            query = """INSERT INTO logs.feeds (source_id, remark, stage) VALUES (%s, %s, %s);"""
            self.db_client.execute(query, (self.ds_id, f"Insert {insert_count} records; update {update_count} records", 1))
            
            # Print summary
            query = f"SELECT COUNT(id) FROM bronze.feeds_{self.ds_name} WHERE log_id = {self.log_id}"
            new_entries_num = self.db_client.execute(query)
            print(f"Insert {insert_count} records; update {update_count} records.")
            print(f"{new_entries_num[0][0]} entries logged into bronze.feeds_{self.ds_name}.")
            self.db_client.close()
            return new_entries_num[0][0]
    
    def store_documents(self, log_id):
        if log_id is None:
            print("No new documents from this feed to store.")
            return
        else:
            self.db_client.connect()
            query = f"SELECT download_url, celex_number FROM bronze.feeds_{self.ds_name} WHERE log_id = {log_id}"
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
                    entries_list = [dict(entry) for entry in self.new_records]
                    self.s3_client.client.put_object(
                            Bucket=self.bucket_name,
                            Key=meta_obj_key,
                            Body=json.dumps(entries_list).encode('utf-8'),
                            ContentType="application/json; charset=utf-8"
                        )
                    print(f"Metadata {log_id}.json uploaded to S3 {self.s3_obj_mtd}.")
                except TypeError as e:
                    print(f"docs_to_insert is None or not iterable:", e)
                    raise
                except Exception as e:
                    print(f"Error in storing documents:", e)
            return
    
    def get_log_id(self):
        return self.log_id
    
    def run(self):
        entries = self.parse()
        new_entries_num = self.log_into_database(entries)
        self.store_documents(self.log_id)
        return new_entries_num
    
if __name__ == "__main__":
    ingestor = EUFeedIngestor()
    ingestor.run()
    # ingestor = EUFeedIngestor()
    # entries = ingestor.parse()
    # for entry in entries:
    #     if entry.title.startswith('CELEX:32021R1230'):
    #         print(entry)