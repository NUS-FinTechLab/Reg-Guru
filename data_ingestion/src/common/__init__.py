"""
Common utilities and base classes for data ingestion pipelines.

This module provides shared functionality across different regional scrapers and pipelines.
"""

# from .BaseScraper import BaseScraper
# from .pipeline_base import IngestionPipeline
# from .helper import (
#     getHtml,
#     getPdfLinks,
#     downloadPdf,
#     downloadPdftoS3,
#     feed_exists_pg,
#     insert_feed_us_pg,
#     insert_feed_if_not_exists_pg
# )
# # from .embedding_helper import (
# #     get_testing_chromadb_client,
# #     get_text_splitter,
# #     embed_texts,
# #     embed_batch,
# #     query_with_date_range
# # )

# __all__ = [
#     'BaseScraper',
#     'IngestionPipeline', 
#     'getHtml',
#     'getPdfLinks',
#     'downloadPdf',
#     'downloadPdftoS3',
#     'feed_exists_pg',
#     'insert_feed_us_pg',
#     'insert_feed_if_not_exists_pg',
#     'get_testing_chromadb_client',
#     'get_text_splitter',
#     'embed_texts',
#     'embed_batch',
#     'query_with_date_range'
# ]