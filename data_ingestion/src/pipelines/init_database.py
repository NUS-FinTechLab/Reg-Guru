from common import DBClient
 
if __name__ == '__main__':
    client = DBClient()
    client.connect()
    queries = [
        # Create schema - ref
        """CREATE SCHEMA IF NOT EXISTS ref;""",
        """CREATE TABLE IF NOT EXISTS ref.data_sources (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL,      -- table name
            code VARCHAR(5) NOT NULL,              -- usually country / region e.g. 'eu', 'sg', 'us'
            description TEXT                       -- optional extra info
        );""",
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
            time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            source_id INT NOT NULL REFERENCES ref.data_sources(id) ON DELETE RESTRICT,
            remark TEXT,
            stage SMALLINT NOT NULL DEFAULT 0 REFERENCES ref.feed_stages(id) ON DELETE RESTRICT
        );""",
        # Create schema - bronze, silver, gold
        """CREATE SCHEMA IF NOT EXISTS bronze;""",
        """CREATE SCHEMA IF NOT EXISTS silver;""",
        """CREATE SCHEMA IF NOT EXISTS gold;"""
    ]
    for statement in queries:
        client.execute(statement)
    client.close()
    print("Database initialised.")