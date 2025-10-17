import os
import pandas as pd
from eu.feed.processor import EUFeedProcessor

class EUHistoryProcessor(EUFeedProcessor):
    def __init__(self, ds_code, batch_size):
        super().__init__(ds_code, batch_size)
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.s3_obj = "data_ingestion/raw/eu/eurlex-feed"

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
        query = f"SELECT * FROM bronze.feeds_{self.ds_code} WHERE log_id = {log_id}"
        new_entries = self.db_client.execute(query)
        meta = pd.DataFrame(new_entries, columns=new_entries[0].keys() if new_entries else [])
        meta['title'] = meta["title"].apply(lambda t: self.clean_title(t) if t else None)
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
    
if __name__ == '__main__':
    processor = EUHistoryProcessor(ds_code='te', batch_size=2)
    for batch in processor.run(91):
        print(batch[0])
        break