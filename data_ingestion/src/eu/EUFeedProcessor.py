import os
import re
import boto3
import pandas as pd
from common.database import db_execute
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv(override=True)
class EUFeedProcessor:
    def __init__(self):
        self.log_id = None
        self.raw_meta_table = 'bronze.feeds_test_eu'
        self.clean_meta_table = 'silver.metadata'

    def clean_metadata(self, log_id): 
        """Prepare ready-to-use metadata in Silver"""
        query = f"SELECT source_id FROM logs.feeds WHERE id = {log_id}"
        source_id = db_execute(query)
        source_id = source_id[0][0]
        query = f"SELECT * FROM {self.raw_meta_table} WHERE log_id = {log_id}" # test
        new_entries = db_execute(query)
        meta = pd.DataFrame(new_entries, columns=new_entries[0].keys() if new_entries else [])
        meta['celex_number'] = meta["title"].apply(lambda t: t.split(':')[1] if t else None)
        for _, row in meta.iterrows():
            query = """
                INSERT INTO silver.metadata (id, source_id, log_id, title, link, published, author, celex_number)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (row['id'], source_id, log_id, row['title'], row['link'], row['published'], row['author'], row['celex_number'])
            db_execute(query, values)
        print("Metadata cleaned and saved to silver.metadata")
        return


# CREATE TABLE IF NOT EXISTS silver.metadata (
#     id INT NOT NULL,
#     source_id INT NOT NULL,
#     log_id INT NOT NULL REFERENCES logs.feeds(id) ON DELETE RESTRICT,
#     title TEXT,
#     link TEXT,
#     published TIMESTAMPTZ,
#     author TEXT,
#     celex_number TEXT,
#     inserted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
#     flag SMALLINT NOT NULL DEFAULT 0,
#     CONSTRAINT pk_silver_metadata PRIMARY KEY (id, source_id),
#     CONSTRAINT fk_log_id FOREIGN KEY (log_id) REFERENCES logs.feeds(id) ON DELETE RESTRICT,
#     CONSTRAINT fk_flag FOREIGN KEY (flag) REFERENCES ref.review_status(id)
# );