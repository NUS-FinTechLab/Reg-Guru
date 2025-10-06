import os
import re
import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv(override=True)

from common.BaseProcessor import BaseProcessor

class EUFeedProcessor(BaseProcessor):
    def __init__(self, ds_code, batch_size=12):
        super().__init__(ds_code, batch_size)
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
        # Fetch new entries from raw metadata table
        query = f"SELECT * FROM bronze.feeds_{self.ds_code} WHERE log_id = {log_id}" # test
        new_entries = self.db_client.execute(query)
        meta = pd.DataFrame(new_entries, columns=new_entries[0].keys() if new_entries else [])
        meta['celex_number'] = meta["title"].apply(lambda t: t.split(':')[1] if t else None)
        meta['title'] = meta["title"].apply(lambda t: self.clean_title(t.split(':')[2]) if t else None)
        for _, row in meta.iterrows():
            query = """
                INSERT INTO silver.metadata (id, source_id, log_id, title, weblink, download_url, published_date, author, unique_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (row['id'], source_id, log_id, row['title'], row['link'], row['link'], row['published'], row['author'], row['celex_number'])
            self.db_client.execute(query, values)
        self.db_client.close()
        print(f"{meta.shape[0]} metadata cleaned and saved to silver.metadata")
        return
    
    def extract_metadata(self, log_id):
        """ Retrieve clean metadata for this feed """
        self.db_client.connect()
        query = f"SELECT title, download_url, published_date, unique_id FROM silver.metadata WHERE log_id = {log_id}"
        try:
            meta = self.db_client.execute(query)
            self.db_client.close()
        except Exception as e:
            print(f"Error retrieving clean metadata for {log_id}: {e}")
            raise
        meta_df = pd.DataFrame([dict(row) for row in meta])
        meta_df['published_date'] = meta_df['published_date'].dt.strftime("%Y-%m-%d")
        print("Clean metadata retrieved")
        return meta_df
    
    def extract_texts(self, key):
        obj = self.s3_client.client.get_object(Bucket=self.bucket_name, Key=key)
        xml_content = obj['Body'].read()
        soup = BeautifulSoup(xml_content, "lxml")
        # Find the main content of regulation
        document = soup.find("div", id="PP4Contents")
        # Remove script and style
        for tag in document(["script", "style"]):
            tag.decompose()
        # Extract texts in p
        paragraphs = []
        for p in document.find_all("p"):
            text = p.get_text(" ", strip=True)
            if text:
                paragraphs.append(text)
        return paragraphs
    
    def _process_a_document(self, log_id, row):
        doc = {}
        key = f"{self.s3_obj}/{log_id}/{row['unique_id']}.xml"
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
                }
        return doc
    
    def run(self, log_id):
        # Clean metadata
        self.clean_metadata(log_id)
        # Extract metadata (feed records)
        new_metadata = self.extract_metadata(log_id) 
        # Process and yield document in records batch by batch
        processed_docs = []
        for _, row in new_metadata.iterrows(): 
            doc = self._process_a_document(log_id, row)
            processed_docs.append(doc)
            if len(processed_docs) == self.batch_size:
                yield processed_docs
                processed_docs = []
        if processed_docs:  # leftover docs
            yield processed_docs
        print(f"All documents are processed")
    
if __name__ == '__main__':
    processor = EUFeedProcessor(ds_code='te', batch_size=2)
    for batch in processor.run(80):
        print(batch[0])
        break