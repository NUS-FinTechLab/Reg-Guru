#!/usr/bin/env python3
"""
ChromaDB Collection Management Script

This script provides functionality to create and manage ChromaDB collections
for different regions (us, eu, sg) in the Reg-Guru system.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from data_ingestion.src.common.embedding_helper import get_testing_chromadb_client


def create_collection(region, collection_name=None):
    """
    Create a ChromaDB collection for the specified region.
    
    Args:
        region (str): The region identifier (us, eu, sg)
        collection_name (str, optional): Custom collection name. Defaults to region_embeddings
    """
    if not collection_name:
        collection_name = f"{region}_embeddings"
    
    try:
        # Get ChromaDB client for the region
        chroma_client = get_testing_chromadb_client(region, f"chromadb_{region}")
        
        # Create or get collection
        collection = chroma_client.get_or_create_collection(name=collection_name)
        
        print(f"Successfully created/accessed collection '{collection_name}' for region '{region}'")
        print(f"Collection count: {collection.count()}")
        
        return collection
        
    except Exception as e:
        print(f"Error creating collection for region '{region}': {str(e)}")
        return None


def list_collections(region):
    """
    List all collections in the ChromaDB for the specified region.
    
    Args:
        region (str): The region identifier (us, eu, sg)
    """
    try:
        chroma_client = get_testing_chromadb_client(region, f"chromadb_{region}")
        collections = chroma_client.list_collections()
        
        print(f"Collections in region '{region}':")
        for collection in collections:
            print(f"  - {collection.name} (count: {collection.count()})")
            
        return collections
        
    except Exception as e:
        print(f"Error listing collections for region '{region}': {str(e)}")
        return []


def delete_collection(region, collection_name):
    """
    Delete a ChromaDB collection for the specified region.
    
    Args:
        region (str): The region identifier (us, eu, sg)
        collection_name (str): Name of the collection to delete
    """
    try:
        chroma_client = get_testing_chromadb_client(region, f"chromadb_{region}")
        chroma_client.delete_collection(name=collection_name)
        
        print(f"Successfully deleted collection '{collection_name}' from region '{region}'")
        
    except Exception as e:
        print(f"Error deleting collection '{collection_name}' from region '{region}': {str(e)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage ChromaDB collections")
    parser.add_argument("action", choices=["create", "list", "delete"], 
                       help="Action to perform")
    parser.add_argument("region", choices=["us", "eu", "sg"], 
                       help="Region identifier")
    parser.add_argument("--collection", type=str, 
                       help="Collection name (required for create/delete)")
    
    args = parser.parse_args()
    
    if args.action == "create":
        create_collection(args.region, args.collection)
    elif args.action == "list":
        list_collections(args.region)
    elif args.action == "delete":
        if not args.collection:
            print("Error: --collection is required for delete action")
            sys.exit(1)
        delete_collection(args.region, args.collection)