#!/usr/bin/env python3
"""
ChromaDB Query Script

This script provides functionality to query ChromaDB collections 
for regulatory information across different regions.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from data_ingestion.src.common.embedding_helper import get_testing_chromadb_client


def query_collection(region, query_text, n_results=5, collection_name=None):
    """
    Query a ChromaDB collection for similar documents.
    
    Args:
        region (str): The region identifier (us, eu, sg)
        query_text (str): The text to search for
        n_results (int): Number of results to return
        collection_name (str, optional): Collection name. Defaults to region_embeddings
    
    Returns:
        dict: Query results from ChromaDB
    """
    if not collection_name:
        collection_name = f"{region}_embeddings"
    
    try:
        # Get ChromaDB client for the region
        chroma_client = get_testing_chromadb_client(region, f"chromadb_{region}")
        
        # Get collection
        collection = chroma_client.get_collection(name=collection_name)
        
        # Perform query
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        print(f"Query: '{query_text}'")
        print(f"Region: {region}")
        print(f"Collection: {collection_name}")
        print(f"Results found: {len(results['documents'][0])}")
        print("-" * 50)
        
        # Display results
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0] if results['metadatas'] else [{}] * len(results['documents'][0]),
            results['distances'][0] if results['distances'] else [0] * len(results['documents'][0])
        )):
            print(f"Result {i+1}:")
            print(f"  Distance: {distance:.4f}")
            print(f"  Metadata: {metadata}")
            print(f"  Document: {doc[:200]}{'...' if len(doc) > 200 else ''}")
            print()
        
        return results
        
    except Exception as e:
        print(f"Error querying collection '{collection_name}' in region '{region}': {str(e)}")
        return None


def get_collection_info(region, collection_name=None):
    """
    Get information about a ChromaDB collection.
    
    Args:
        region (str): The region identifier (us, eu, sg)
        collection_name (str, optional): Collection name. Defaults to region_embeddings
    """
    if not collection_name:
        collection_name = f"{region}_embeddings"
    
    try:
        chroma_client = get_testing_chromadb_client(region, f"chromadb_{region}")
        collection = chroma_client.get_collection(name=collection_name)
        
        print(f"Collection Information:")
        print(f"  Name: {collection.name}")
        print(f"  Count: {collection.count()}")
        print(f"  Region: {region}")
        
        # Get a sample of documents
        if collection.count() > 0:
            sample = collection.get(limit=3)
            print(f"  Sample documents:")
            for i, doc in enumerate(sample['documents']):
                print(f"    {i+1}. {doc[:100]}{'...' if len(doc) > 100 else ''}")
        
    except Exception as e:
        print(f"Error getting info for collection '{collection_name}' in region '{region}': {str(e)}")


def search_regulatory_info(query_text, regions=None, n_results=3):
    """
    Search for regulatory information across multiple regions.
    
    Args:
        query_text (str): The regulatory query
        regions (list, optional): List of regions to search. Defaults to all regions
        n_results (int): Number of results per region
    
    Returns:
        dict: Results from all regions
    """
    if not regions:
        regions = ["us", "eu", "sg"]
    
    all_results = {}
    
    print(f"Searching for: '{query_text}'")
    print("=" * 60)
    
    for region in regions:
        print(f"\n{region.upper()} REGION:")
        print("-" * 20)
        
        results = query_collection(region, query_text, n_results)
        all_results[region] = results
    
    return all_results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Query ChromaDB collections")
    parser.add_argument("action", choices=["query", "info", "search"], 
                       help="Action to perform")
    parser.add_argument("--region", choices=["us", "eu", "sg"], 
                       help="Region identifier (required for query/info)")
    parser.add_argument("--query", type=str, 
                       help="Query text (required for query/search)")
    parser.add_argument("--collection", type=str, 
                       help="Collection name (optional)")
    parser.add_argument("--results", type=int, default=5,
                       help="Number of results to return (default: 5)")
    parser.add_argument("--regions", nargs="+", choices=["us", "eu", "sg"],
                       help="Regions to search (for search action)")
    
    args = parser.parse_args()
    
    if args.action == "query":
        if not args.region or not args.query:
            print("Error: --region and --query are required for query action")
            sys.exit(1)
        query_collection(args.region, args.query, args.results, args.collection)
        
    elif args.action == "info":
        if not args.region:
            print("Error: --region is required for info action")
            sys.exit(1)
        get_collection_info(args.region, args.collection)
        
    elif args.action == "search":
        if not args.query:
            print("Error: --query is required for search action")
            sys.exit(1)
        search_regulatory_info(args.query, args.regions, args.results)