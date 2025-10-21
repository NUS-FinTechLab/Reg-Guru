import os
import boto3
import requests
from botocore.exceptions import ClientError

class S3Client:
    def __init__(self):
        self.client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        return
    
    def store_pdf(self, url, bucket, dest_key):
        """Puts a PDF from a given URL as an S3 object specified by the object key."""

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=50)
            response.raise_for_status()

            self.client.put_object(
                Bucket=bucket,
                Key=dest_key,
                Body=response.content,
                ContentType="application/pdf"
            )

        except requests.HTTPError as e:
            print("Download failed:", e)
        except ClientError as e:
            print("S3 upload failed:", e)
        return