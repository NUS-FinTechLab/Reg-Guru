import os
import io
import pdfplumber
import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv(override=True)

from ...common.BaseProcessor import BaseProcessor


class SsoProcessor(BaseProcessor):
    def __init__(self, ds_code, batch_size=12):
        super().__init__(ds_code, batch_size)
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.s3_obj = "data_ingestion/raw/sg/sso"

    def clean_metadata(self, log_id):
        """Prepare ready-to-use metadata in schema Silver"""
        if self.check_if_metadata_cleaned(log_id):
            # If clean metadata exists, skip
            print(f"Clean metadata already exist")
            return

        self.db_client.connect()
        # Retrieve data source id
        query = f"SELECT source_id FROM logs.feeds WHERE id = {log_id}"
        source_id = self.db_client.execute(query)[0][0]
        # Fetch new entries from raw metadata table
        query = (
            f"SELECT * FROM bronze.feeds_{self.ds_code} WHERE log_id = {log_id}"  # test
        )
        new_entries = self.db_client.execute(query)
        meta = pd.DataFrame(
            new_entries, columns=new_entries[0].keys() if new_entries else []
        )
        for _, row in meta.iterrows():
            query = """
                INSERT INTO silver.metadata (id, source_id, log_id, title, weblink, download_url, published_date, valid_date, unique_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                row["id"],
                source_id,
                log_id,
                row["title"],
                row["weblink"],
                row["pdf_url"],
                row["published_date"],
                row["valid_date"],
                row["doc_id"],
            )
            self.db_client.execute(query, values)
        self.db_client.close()
        print(f"{meta.shape[0]} metadata cleaned and saved to silver.metadata")
        return

    def extract_metadata(self, log_id):
        """Retrieve clean metadata for this feed"""
        self.db_client.connect()
        query = f"SELECT title, download_url, published_date, valid_date, unique_id FROM silver.metadata WHERE log_id = {log_id}"
        try:
            meta = self.db_client.execute(query)
            self.db_client.close()
        except Exception as e:
            print(f"Error retrieving clean metadata for {log_id}: {e}")
            raise
        meta_df = pd.DataFrame([dict(row) for row in meta])
        meta_df["published_date"] = pd.to_datetime(
            meta_df["published_date"], errors="raise"
        ).apply(lambda x: int(x.timestamp()) if pd.notnull(x) else None)
        meta_df["valid_date"] = pd.to_datetime(
            meta_df["valid_date"], errors="raise"
        ).apply(lambda x: int(x.timestamp()) if pd.notnull(x) else None)
        print("Clean metadata retrieved")
        return meta_df

    def extract_texts(self, key):
        """Download and extract texts from a document on S3"""
        chunks = []
        response = self.s3_client.client.head_object(Bucket=self.bucket_name, Key=key)
        content_type = response.get("ContentType")
        main_type = content_type.split(";")[0].strip()
        try:
            if main_type == "application/pdf":
                pdf_obj = self.s3_client.client.get_object(
                    Bucket=self.bucket_name, Key=key
                )
                pdf_bytes = pdf_obj["Body"].read()
                pdf_file = io.BytesIO(pdf_bytes)

                # Open with pdfplumber
                with pdfplumber.open(pdf_file) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            chunks.append(text.strip())

            # elif main_type == 'text/html':
            #     charset = content_type.split("charset=")[-1].strip() if "charset=" in content_type else 'utf-8'
            #     obj = self.s3_client.client.get_object(Bucket=self.bucket_name, Key=key)
            #     html_bytes = obj["Body"].read()
            #     html_str = html_bytes.decode(charset)
            #     soup = BeautifulSoup(html_str, "html.parser")
            #     for tag in soup(["script", "style"]):
            #         tag.decompose()

            #     text = soup.get_text()
            #     if text.strip():
            #         chunks.append(text.strip())

            else:
                print(f"Unsupported content type {main_type} for key {key}")
        except Exception as e:
            print(f"Error processing {key}: {str(e)}")
            raise
        return chunks

    def _process_a_document(self, log_id, row):
        doc = {}
        key = f"{self.s3_obj}/{log_id}/{row['unique_id']}.pdf"
        # print(f"Processing {key} ...")
        raw_texts = self.extract_texts(key)
        if len(raw_texts) == 0:
            print(f"No texts to process [{key}]")
        else:
            text = "\n".join(self.clean_texts(raw_texts))
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


if __name__ == "__main__":
    processor = SsoProcessor(ds_code="te", batch_size=2)
    for batch in processor.run(45):
        print(batch[0])
        break
