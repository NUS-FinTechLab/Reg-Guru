#!/usr/bin/env python3
"""
ChromaDB helper script for querying different regions.
This script handles the chromadb operations in the proper environment.
"""
import sys
import os
import json

# Add the data_ingestion directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
data_ingestion_path = os.path.join(script_dir, '..', 'data_ingestion')
sys.path.insert(0, data_ingestion_path)

def query_chromadb(user_message, region="us", n_results=5):
    """Query ChromaDB collection for relevant documents."""
    try:
        from src.common.embedding_helper import get_testing_chromadb_client, embed_texts
        
        chroma_client = get_testing_chromadb_client(region, f"chromadb_{region}")
        collection = chroma_client.get_or_create_collection(name=f"{region}_embeddings")
        
        if collection.count() == 0:
            return {"error": f"No documents found in {region} region collection"}
        
        # Use the same embedding model that was used to create the collection
        query_embedding = embed_texts([user_message])
        
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        
        # Extract documents from results
        documents = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
        distances = results.get('distances', [[]])[0]
        
        # Combine documents with metadata for context
        relevant_docs = []
        for doc, metadata, distance in zip(documents, metadatas, distances):
            relevant_docs.append({
                'content': doc,
                'metadata': metadata,
                'distance': distance
            })
        
        return {
            "success": True,
            "documents": relevant_docs,
            "count": len(relevant_docs)
        }
        
    except Exception as e:
        return {"error": f"Error querying ChromaDB for region {region}: {str(e)}"}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python chromadb_query.py <message> <region> [n_results]")
        sys.exit(1)
    
    message = sys.argv[1]
    region = sys.argv[2]
    n_results = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    result = query_chromadb(message, region, n_results)
    print(json.dumps(result, indent=2))