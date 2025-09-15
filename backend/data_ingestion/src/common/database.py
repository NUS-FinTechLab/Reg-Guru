import os
import psycopg2
import psycopg2.extras

from dotenv import load_dotenv
load_dotenv(override=True)

# It's recommended to separate statements into a list and execute them one by one.
# Don't let cursor execute a single long query with multiple statements separated by semicolon - it may lead to errors.
def db_execute(statement, params=None):
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dbname=os.getenv("DB_NAME")
    )

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if params:
        cur.execute(statement, params)
    else:
        cur.execute(statement)
    if cur.description:
        result = cur.fetchall()
    else:
        result = None

    conn.commit()
    cur.close()
    conn.close()
    return result

query = [
    # Create schema - ref
    """CREATE SCHEMA IF NOT EXISTS ref;""",
    """CREATE TABLE IF NOT EXISTS ref.data_sources (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,           -- short name
        code CHAR(2) NOT NULL,  -- country / region e.g. 'EU', 'SG', 'US'
        description TEXT                     -- optional extra info
    );""",
    """INSERT INTO ref.data_sources (name, code, description) VALUES
        ('eurlex feed', 'EU', 'European Union official publications and legal');""",     
    """CREATE TABLE IF NOT EXISTS ref.review_status (
        id SMALLINT PRIMARY KEY,
        description TEXT
    );""",
    """INSERT INTO ref.review_status (id, description) VALUES
        (0, 'Normal'),
        (1, 'Pending review'),
        (2, 'Rejected');""",
    """CREATE TABLE IF NOT EXISTS ref.feed_stages (
        id SMALLINT PRIMARY KEY,
        description TEXT NOT NULL);""",
    """INSERT INTO ref.feed_stages (id, description) VALUES
        (0, 'start'),
        (1, 'success'),
        (2, 'error');
    """,
    # Create schema - logs
    """CREATE SCHEMA IF NOT EXISTS logs;""",
    """CREATE TABLE IF NOT EXISTS logs.feeds (
        id SERIAL PRIMARY KEY,
        time TIMESTAMTZ NOT NULL DEFAULT NOW(),
        source_id TEXT NOT NULL REFERENCES ref.data_sources(id) ON DELETE RESTRICT,
        remark TEXT,
        stage SMALLINT NOT NULL DEFAULT 0 REFERENCES ref.feed_stages(id) ON DELETE RESTRICT
    );""",
    # Create schema - bronze, silver, gold
    """CREATE SCHEMA IF NOT EXISTS bronze;""",
    """CREATE SCHEMA IF NOT EXISTS silver;""",
    """CREATE SCHEMA IF NOT EXISTS gold;""",
    """CREATE TABLE IF NOT EXISTS bronze.feeds_test_eu (
        id SERIAL PRIMARY KEY,
        log_id INT NOT NULL REFERENCES logs.feeds(id) ON DELETE RESTRICT,
        title TEXT,
        summary TEXT,
        link TEXT,
        uri_id TEXT,
        guidislink BOOLEAN,
        published TIMESTAMPTZ,
        author TEXT,
        inserted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        flag SMALLINT NOT NULL DEFAULT 0 REFERENCES ref.review_status(id),
        remark TEXT
        );"""
]
# for statement in query:
#     db_execute(query)

if __name__ == "__main__":
    print("Initialise database.")