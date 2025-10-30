import os
import pandas as pd
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv
load_dotenv(override=True)

class DBClient:
    def __init__(self):
        self.conn = None

    def connect(self):
        if self.conn is None or self.conn.closed != 0:
            try:
                self.conn = psycopg2.connect(
                    host=os.getenv("DB_HOST"),
                    port=os.getenv("DB_PORT"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    dbname=os.getenv("DB_NAME")
                )
            except Exception as e:
                print(f"Could not connect to database: {str(e)}")
                raise
        return

    def execute(self, statement, params=None):
        """Execute an SQL statement with optional parameters"""
        if self.conn is None:
            raise Exception("Database connection is not established.")
        else:
            with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                try:
                    if params:
                        params = [None if (p is pd.NaT or pd.isna(p)) else p for p in params] # Handle NaT and NaN
                        cur.execute(statement, params)
                    else:
                        cur.execute(statement)
                except Exception as e:
                    print(f"Error executing: {statement} with params: {params}\nError: {e}")
                    self.conn.rollback()
                    raise
                if cur.description:
                    return cur.fetchall()
                else:
                    return None

    def close(self):
        """Commit changes and close the database connection"""
        if self.conn:
            try:
                self.conn.commit()
                self.conn.close()
            except Exception as e:
                print(f"Error closing database connection: {str(e)}")
        return
    
    def rollback(self):
        """Rollback the current transaction"""
        if self.conn:
            try:
                self.conn.rollback()
            except Exception as e:
                print(f"Error rolling back transaction: {str(e)}")
        return
    
if __name__ == "__main__":
    db_client = DBClient()
    db_client.connect()
    query = f"""SELECT * FROM bronze.feeds_eu_eurlex_test"""
    records = db_client.execute(query)
    db_client.close()
    for rec in records:
        print(dict(rec))
    