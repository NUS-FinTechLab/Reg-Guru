from eu.EUFeedIngestor import EUFeedIngestor
from common.database import db_execute
query = "TRUNCATE TABLE bronze.feeds_test_eu"
db_execute(query)
ingestor = EUFeedIngestor("https://eur-lex.europa.eu/EN/display-feed.rss?myRssId=zqe48ppy80IwdPmk3XxQMlkGOfbi%2BE8KLQfclbDnbig%3D")
ingestor.run()