import os
import shutil
import csv
from datetime import datetime
from hashlib import md5
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from apscheduler.schedulers.background import BackgroundScheduler
from .config import (
    VECTORSTORE_DIRECTORY, TEMP_DIR, FEEDBACK_DB, BACKUP_DIR,
    MODEL_NAME, MODEL_TEMPERATURE, RETRIEVAL_K, PROMPT_TEMPLATE
)
from .helper import get_chroma_collection

# Initialize LLM components
llm = ChatOpenAI(model=MODEL_NAME, temperature=MODEL_TEMPERATURE)
embeddings = OpenAIEmbeddings()
prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

# Initialize backup scheduler
scheduler = BackgroundScheduler()

def get_file_hash(file_path):
    """Get MD5 hash of a file."""
    with open(file_path, 'rb') as f:
        return md5(f.read()).hexdigest()

def initialize_directories():
    """Create necessary directories and files."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if not os.path.exists(FEEDBACK_DB):
        with open(FEEDBACK_DB, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "query", "response", "rating", "comments"])

def cleanup_temp():
    """Clean up temporary files and shutdown scheduler."""
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    if scheduler.running:
        scheduler.shutdown()

def process_chat_query(user_message, region="us"):
    """Process chat query using ChromaDB for a specific region."""
    if not user_message.strip():
        raise ValueError("Empty message")
    
    try:
        # Retrieve respective ChromaDB collection based on region
        collection = get_chroma_collection(region)
        
        if collection.count() == 0:
            raise FileNotFoundError(f"No documents found in {region} region collection")
        
        # Query the collection for relevant documents
        results = collection.query(
            query_texts=[user_message],
            n_results=RETRIEVAL_K
        )
        
        # Extract documents from results
        documents = results.get('documents', [[]])[0]
        
        if not documents:
            return f"No relevant documents found for your query in the {region} region.", {'sources': []}
        
        # Construct prompt with retrieved documents using the template
        context = "\n\n".join(documents)
        
        # Use the prompt template from config
        formatted_prompt = prompt.format(context=context, question=user_message)
        
        # Get response from LLM
        response = llm.invoke(formatted_prompt)
        
        # Extract source information for frontend display
        metadatas = results.get('metadatas', [[]])[0]
        sources = []
        seen_links = set()  # To avoid duplicate links
        
        for metadata in metadatas:
            if metadata and 'link' in metadata and 'title' in metadata:
                link = metadata['link']
                title = metadata['title']
                # Only add unique links
                if link not in seen_links:
                    sources.append({
                        'title': title,
                        'link': link
                    })
                    seen_links.add(link)
        
        # Return the response
        response_content = response.content if hasattr(response, 'content') else str(response)
        return response_content, {'sources': sources}
        
    except Exception as e:
        print(f"Error processing query for region {region}: {str(e)}")
        raise Exception(f"Failed to process query for {region} region: {str(e)}")

def log_feedback(query, response, rating, comments=""):
    """Log user feedback to CSV file."""
    valid_ratings = ['thumbs_up', 'thumbs_down']
    
    if rating.lower() not in valid_ratings:
        raise ValueError("Invalid rating type")

    with open(FEEDBACK_DB, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            query.strip(),
            response.strip(),
            rating.lower(),
            comments.strip()
        ])

def query_chroma_collection(user_message, region="us", n_results=5):
    """
    Query ChromaDB collection for relevant documents.
    
    Args:
        user_message (str): The user's query
        region (str): Region to query (us, eu, sg)
        n_results (int): Number of results to return
    
    Returns:
        list: List of relevant documents from ChromaDB
    """
    try:
        collection = get_chroma_collection(region)
        
        if collection.count() == 0:
            print(f"No documents found in {region} region collection")
            return []
        
        results = collection.query(
            query_texts=[user_message],
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
        
        print(f"Found {len(relevant_docs)} relevant documents from {region} region")
        return relevant_docs
        
    except Exception as e:
        print(f"Error querying ChromaDB for region {region}: {str(e)}")
        return []

def process_chat_query_with_chroma(user_message, regions=None, use_faiss=True):
    """
    Process chat query using both FAISS and ChromaDB collections.
    
    Args:
        user_message (str): The user's query
        regions (list): List of regions to query in ChromaDB
        use_faiss (bool): Whether to also use FAISS vectorstore
    
    Returns:
        str: Response combining information from multiple sources
    """
    if not user_message.strip():
        raise ValueError("Empty message")
    
    all_docs = []
    
    # Query ChromaDB collections if regions specified
    if regions:
        for region in regions:
            chroma_docs = query_chroma_collection(user_message, region)
            all_docs.extend(chroma_docs)
    
    # Use FAISS if requested and available
    faiss_response = None
    if use_faiss and os.path.exists(os.path.join(VECTORSTORE_DIRECTORY, "index.faiss")):
        try:
            faiss_response = process_chat_query(user_message)
        except Exception as e:
            print(f"Error with FAISS query: {str(e)}")
    
    # If we have ChromaDB results, create a combined response
    if all_docs:
        context_docs = [doc['content'] for doc in all_docs[:RETRIEVAL_K]]
        context = "\n\n".join(context_docs)
        
        # Use the prompt template from config
        formatted_prompt = prompt.format(context=context, question=user_message)
        
        try:
            response = llm.invoke(formatted_prompt)
            combined_response = response.content if hasattr(response, 'content') else str(response)
            
            # If we also have FAISS response, mention it
            if faiss_response:
                combined_response += f"\n\nAdditional context: {faiss_response}"
            
            return combined_response
        except Exception as e:
            print(f"Error generating ChromaDB response: {str(e)}")
    
    # Fallback to FAISS if available
    if faiss_response:
        return faiss_response
    
    # Final fallback
    if not all_docs and not faiss_response:
        raise FileNotFoundError("No documents available in any source")
    
    return "I found some relevant information but couldn't process it properly. Please try again."