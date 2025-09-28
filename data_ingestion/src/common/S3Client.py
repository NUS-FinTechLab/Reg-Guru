import os
import boto3

class S3Client:
    def __init__(self):
        self.client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY")
        )
        return