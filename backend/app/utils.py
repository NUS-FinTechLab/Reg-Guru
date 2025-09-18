import os
import shutil
import json
import csv
from datetime import datetime
from hashlib import md5
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate
from apscheduler.schedulers.background import BackgroundScheduler
from .config import (
    TEMP_DIR, QUERIES_FILE, FEEDBACK_DB, BACKUP_DIR,
    MODEL_NAME, MODEL_TEMPERATURE, RETRIEVAL_K, PROMPT_TEMPLATE
)

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

def load_queries():
    """Load saved queries from JSON file."""
    try:
        with open(QUERIES_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_queries(queries):
    """Save queries to JSON file."""
    with open(QUERIES_FILE, 'w') as f:
        json.dump(queries, f)

def process_chat_query(user_message, region):
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

def save_query_record(question, answer, document="Current Document"):
    """Save a query record to the queries file."""
    queries = load_queries()
    queries.append({
        "question": question,
        "answer": answer,
        "timestamp": datetime.now().isoformat(),
        "document": document
    })
    save_queries(queries)

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