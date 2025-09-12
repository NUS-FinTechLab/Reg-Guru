import datetime
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, src_dir)

from common.embedding_helper import embed_batch, get_testing_chromadb_client, query_with_date_range

FINCEN_COLLECTION_NAME = "fincen_embeddings"

def main():
    chromadb_client = get_testing_chromadb_client('us', 'chromadb_fincen')
    test_collection = chromadb_client.get_collection(name=FINCEN_COLLECTION_NAME)
    query_texts="A customer transfers or receives funds, including through traditional banking systems, to or from an unregistered foreign CVC exchange or other MSB with no relation to where the customer lives or conducts business."

    results = query_with_date_range(test_collection, query_texts, datetime.datetime(2010, 1, 1), datetime.datetime(2025, 1, 1), n_results=5)

    print(results)
    
if __name__ == "__main__":
    main()