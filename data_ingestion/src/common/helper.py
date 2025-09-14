import requests
from bs4 import BeautifulSoup
import os
import sqlite3
import psycopg2

def getHtml(url):
    r"""Sends a GET request.
    """
    response = requests.get(url, timeout=50)
    response.raise_for_status()
    
    return response.text

def getPdfLinks(url):
    r"""Extracts all PDF links from a given URL.
    """
    html = getHtml(url)
    soup = BeautifulSoup(html, 'html.parser')
    
    pdfLinks = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.lower().endswith('.pdf'):
            pdfLinks.add(href)
    
    return pdfLinks

def downloadPdf(url, dest_path):
    r"""Downloads a PDF from a given URL to the specified destination path.
    """
    response = requests.get(url, stream=True, timeout=50)
    response.raise_for_status()
    
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
# PostgreSQL-compatible helper functions
def feed_exists_pg(conn, url, title):
    r"""Checks if a feed with the same URL and title already exists in the PostgreSQL database.
    
    Args:
        conn: PostgreSQL database connection
        url: The URL to check
        title: The title to check
        
    Returns:
        bool: True if feed exists, False otherwise
    """
    sql = ''' SELECT COUNT(*) FROM bronze.feeds_us 
              WHERE url = %s AND title = %s '''
    cur = conn.cursor()
    cur.execute(sql, (url, title))
    count = cur.fetchone()[0]
    return count > 0

def insert_feed_us_pg(conn, feed):
    r"""Inserts a feed record into the PostgreSQL database.
    """
    sql = ''' INSERT INTO bronze.feeds_us(id, url, timestamp, title, inserted_at)
              VALUES(%s,%s,%s,%s,%s) '''
    cur = conn.cursor()
    cur.execute(sql, feed)
    conn.commit()
    return cur.rowcount

def insert_feed_if_not_exists_pg(conn, feed):
    r"""Inserts a feed record only if it doesn't already exist in PostgreSQL.
    
    Args:
        conn: PostgreSQL database connection
        feed: Tuple containing (id, url, timestamp, title, inserted_at)
        
    Returns:
        tuple: (was_inserted: bool, row_id: int or None)
               was_inserted is True if new record was inserted
               row_id is the ID of the inserted record, or None if already existed
    """
    # Extract url and title from the feed tuple
    _, url, _, title, _ = feed
    
    # Check if feed already exists
    if feed_exists_pg(conn, url, title):
        return (False, None)
    
    # If not exists, insert it
    row_count = insert_feed_us_pg(conn, feed)
    return (True, row_count)