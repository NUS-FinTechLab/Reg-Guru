import sys
import os
import json
import subprocess

def get_chroma_collection(region):
    """Get ChromaDB collection for a specific region using subprocess."""
    try:
        # Use the .venv-bgem3 Python environment to run the chromadb query script
        python_path = "/home/monngd/Reg-Guru/data_ingestion/.venv-bgem3/bin/python"
        script_path = "/home/monngd/Reg-Guru/scripts/chromadb_query.py"
        
        # Test query to check if collection exists
        result = subprocess.run(
            [python_path, script_path, "test", region, "1"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise Exception(f"ChromaDB script failed: {result.stderr}")
        
        response = json.loads(result.stdout)
        if "error" in response:
            raise Exception(response["error"])

        return ChromaDBCollection(region, python_path, script_path)
        
    except Exception as e:
        print(f"Error getting collection for region {region}: {str(e)}")
        raise e

class ChromaDBCollection:
    """Mock ChromaDB collection that uses subprocess to query."""
    
    def __init__(self, region, python_path, script_path):
        self.region = region
        self.python_path = python_path
        self.script_path = script_path
    
    def query(self, query_texts, n_results=5):
        """Query the collection using subprocess."""
        try:
            query_text = query_texts[0] if isinstance(query_texts, list) else query_texts
            
            result = subprocess.run(
                [self.python_path, self.script_path, query_text, self.region, str(n_results)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise Exception(f"ChromaDB query failed: {result.stderr}")
            
            response = json.loads(result.stdout)
            if "error" in response:
                raise Exception(response["error"])
            
            # Convert back to chromadb format
            documents = []
            metadatas = []
            distances = []
            
            for doc in response.get("documents", []):
                documents.append(doc["content"])
                metadatas.append(doc["metadata"])
                distances.append(doc["distance"])
            
            return {
                "documents": [documents],
                "metadatas": [metadatas],
                "distances": [distances]
            }
            
        except Exception as e:
            print(f"Error querying collection: {str(e)}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
    
    def count(self):
        """Get document count in collection."""
        try:
            # Use a simple test query to check if documents exist
            result = self.query(["test"], n_results=1)
            return len(result.get("documents", [[]])[0])
        except:
            return 0