import os
import shutil
import csv
from datetime import datetime
from hashlib import md5
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
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

def process_chat_query(user_message):
    """Process a chat query using the RAG system."""
    if not user_message.strip():
        raise ValueError("Empty message")

    if not os.path.exists(os.path.join(VECTORSTORE_DIRECTORY, "index.faiss")):
        raise FileNotFoundError("No documents uploaded yet")

    print("Loading vectorstore...")
    vectorstore = FAISS.load_local(
        folder_path=VECTORSTORE_DIRECTORY,
        embeddings=embeddings,
        allow_dangerous_deserialization=True
    )
    print("Vectorstore loaded successfully.")

    print("Initializing QA chain...")
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": RETRIEVAL_K}),
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=False
    )
    print("QA chain initialized successfully.")

    print(f"Processing query: {user_message}")
    response = qa_chain.invoke({"query": user_message})
    print(f"Query processed successfully. Response: {response}")

    return response["result"]

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
        
        enhanced_prompt = f"""Based on the following regulatory documents, please answer the user's question:

Context from regulatory documents:
{context}

User question: {user_message}

Please provide a comprehensive answer based on the regulatory information provided above."""
        
        try:
            response = llm.invoke(enhanced_prompt)
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