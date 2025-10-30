import os
import re
import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv(override=True)

from common.BaseProcessor import BaseProcessor

class EUFeedProcessor(BaseProcessor):
    def __init__(self, ds_name, batch_size, test_mode):
        super().__init__(ds_name, batch_size, test_mode)
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.s3_obj = "data_ingestion/raw/eu/eurlex-feed"

    def clean_title(self, text):
        text = text.replace("\xa0", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n+", "\n", text)
        text = text.strip()
        return text

    def clean_metadata(self, log_id):
        """Prepare ready-to-use metadata in Silver"""
        if self.check_if_metadata_cleaned(log_id):
            # If clean metadata exists, skip
            print(f"Clean metadata already exist")
            return
        
        self.db_client.connect()
        # Retrieve data source id
        query = f"SELECT source_id FROM logs.feeds WHERE id = {log_id}"
        source_id = self.db_client.execute(query)[0][0]
        # Fetch new entries from the raw table
        query = f"SELECT * FROM bronze.feeds_{self.ds_name} WHERE log_id = {log_id} AND flag = 0"
        new_entries = self.db_client.execute(query)
        meta = pd.DataFrame([dict(entry) for entry in new_entries])
        meta['title'] = meta["title"].apply(lambda t: self.clean_title(t) if t else None)
        for _, row in meta.iterrows():
            query = f"""
                INSERT INTO {self.metadata_table} (id, source_id, log_id, title, weblink, download_url, published_date, valid_date, author, unique_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                row['id'],
                source_id, 
                log_id, 
                row['title'], 
                row['link'], 
                row['download_url'], 
                row['published'] if pd.notna(row['published']) else None, 
                row['valid_date'] if pd.notna(row['latest_consolidated']) else None, 
                row['author'], 
                row['celex_number']
            )
            self.db_client.execute(query, values)
        self.db_client.close()
        print(f"{meta.shape[0]} metadata cleaned and saved to {self.metadata_table}")
        return
    
    def extract_metadata(self, log_id):
        """ Retrieve clean metadata for this feed """
        self.db_client.connect()
        query = f"SELECT title, download_url, published_date, valid_date, unique_id FROM {self.metadata_table} WHERE log_id = {log_id} AND flag = 0"
        try:
            meta = self.db_client.execute(query)
            self.db_client.close()
        except Exception as e:
            print(f"Error retrieving clean metadata for {log_id}: {e}")
            raise
        meta_df = pd.DataFrame([dict(row) for row in meta])
        meta_df['published_date'] = meta_df['published_date'].apply(lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else None)
        meta_df['valid_date'] = meta_df.apply(lambda x: x['valid_date'].strftime("%Y-%m-%d") if pd.notna(x['valid_date']) else x['published_date'], axis=1)
        print("Clean metadata retrieved")
        return meta_df
    
    def extract_texts(self, key):
        obj = self.s3_client.client.get_object(Bucket=self.bucket_name, Key=key)
        content = obj['Body'].read()
        soup = BeautifulSoup(content, "html.parser")
        if soup is None:
            print("No content from document: ", key)
            return []
        # Remove script and style
        for tag in soup(["script", "style"]):
            tag.decompose()
        # Extract texts in p
        paragraphs = []
        for p in soup.find_all("p"):
            text = p.get_text(" ", strip=True)
            if text:
                paragraphs.append(text)
        return paragraphs
    
    def _process_a_document(self, log_id, row):
        doc = {}
        key = f"{self.s3_obj}/{log_id}/{row['unique_id']}.html"
        # print(f"Processing {key} ...")
        raw_texts = self.extract_texts(key)
        if len(raw_texts) == 0:
            print(f"No texts to process [{key}]")
        else:
            text = '\n'.join(self.clean_texts(raw_texts))
            if len(text) == 0:
                print(f"No texts to process [{key}] after cleaning")
            else:
                doc = { 
                    "content": text,
                    "metadata": row.to_dict(),
                    "unique_id": self.ds_name + ":" + row['unique_id']
                }
        return doc
    
    def run(self, log_id):
        # Clean metadata
        self.clean_metadata(log_id)
        # Extract metadata (feed records)
        new_metadata = self.extract_metadata(log_id) 
        # Process and yield document in records batch by batch
        processed_docs = []
        for _, row in new_metadata.iterrows(): # Continue from error
            doc = self._process_a_document(log_id, row)
            if doc != {}:
                processed_docs.append(doc)
            if len(processed_docs) == self.batch_size:
                yield processed_docs
                processed_docs = []
        if processed_docs:  # leftover docs
            yield processed_docs
        print("All documents are processed")

if __name__ == '__main__':
    processor = EUFeedProcessor(ds_name='eu_eurlex_test', batch_size=1)
    for batch in processor.run(116):
        print(batch[0])
        break