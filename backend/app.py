from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import atexit
import shutil
import json
from dotenv import load_dotenv
from datetime import datetime
from upload_document import DocumentUploader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate
import csv
from hashlib import md5
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@app.route('/api/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    response = jsonify({'success': True})
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response

# Configuration
VECTORSTORE_DIRECTORY = "Database"
TEMP_DIR = "temp"
QUERIES_FILE = "saved_queries.json"
FEEDBACK_DB = "feedback_logs.csv"
BACKUP_DIR = "feedback_backups"
DOCUMENTS_LIST_FILE = "uploaded_documents.json"

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Initialize components
uploader = DocumentUploader(vectorstore_directory=VECTORSTORE_DIRECTORY)
llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
embeddings = OpenAIEmbeddings()

# Document tracking functions
def load_uploaded_documents():
    try:
        with open(DOCUMENTS_LIST_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_uploaded_document(filename, file_hash):
    documents = load_uploaded_documents()
    documents.append({
        "filename": filename,
        "hash": file_hash,
        "upload_time": datetime.now().isoformat()
    })
    with open(DOCUMENTS_LIST_FILE, 'w') as f:
        json.dump(documents, f)

def get_file_hash(file_path):
    with open(file_path, 'rb') as f:
        return md5(f.read()).hexdigest()

# Ensure directories exist
os.makedirs(BACKUP_DIR, exist_ok=True)
if not os.path.exists(FEEDBACK_DB):
    with open(FEEDBACK_DB, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "query", "response", "rating", "comments"])

# Feedback Backup Function
def backup_feedback():
    if os.path.exists(FEEDBACK_DB):
        backup_path = os.path.join(BACKUP_DIR, f"feedback_{datetime.now().date()}.csv")
        shutil.copy2(FEEDBACK_DB, backup_path)

# Initialise backup scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(backup_feedback, 'cron', hour=0)
scheduler.start()

# Query Storage Functions
def load_queries():
    try:
        with open(QUERIES_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_queries(queries):
    with open(QUERIES_FILE, 'w') as f:
        json.dump(queries, f)

# Prompt template
prompt_template = """Answer the question in a concise manner based on the following context:
{context}

Question: {question}

If the context does not contain the answer, use other sources.
"""
prompt = ChatPromptTemplate.from_template(prompt_template)

# Cleanup function
def cleanup_temp():
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    if scheduler.running:
        scheduler.shutdown()

atexit.register(cleanup_temp)

# API Endpoints
@app.route('/api/upload_document', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "Empty file name"}), 400

    try:
        os.makedirs(TEMP_DIR, exist_ok=True)
        temp_path = os.path.join(TEMP_DIR, file.filename)
        file.save(temp_path)
        
        # Check for duplicates
        current_hash = get_file_hash(temp_path)
        existing_docs = load_uploaded_documents()
        
        if any(doc['hash'] == current_hash for doc in existing_docs):
            os.remove(temp_path)
            return jsonify({"error": "File already exists in database"}), 409
        
        # Process new file
        uploader.upload_documents([temp_path])
        save_uploaded_document(file.filename, current_hash)
        os.remove(temp_path)
        
        return jsonify({
            "message": "Document processed successfully",
            "filename": file.filename
        }), 200
    except Exception as e:
        return jsonify({"error": f"Document processing failed: {str(e)}"}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    print("Received data:", data) 
    user_message = data.get("message", {}).get("text", "").strip()
    
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    try:
        if not os.path.exists(os.path.join(VECTORSTORE_DIRECTORY, "index.faiss")):
            return jsonify({"error": "No documents uploaded yet"}), 404

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
            retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=False
        )
        print("QA chain initialized successfully.")

        print(f"Processing query: {user_message}")
        response = qa_chain.invoke({"query": user_message})
        print(f"Query processed successfully. Response: {response}")

        return jsonify({"response": response["result"]}), 200
    except Exception as e:
        print(f"Error during query processing: {str(e)}")
        return jsonify({"error": f"Failed to process query: {str(e)}"}), 500

@app.route('/api/save_query', methods=['POST'])
def save_query():
    data = request.json
    queries = load_queries()
    
    queries.append({
        "question": data.get("question"),
        "answer": data.get("answer"),
        "timestamp": datetime.now().isoformat(),
        "document": data.get("document", "Current Document")
    })
    
    save_queries(queries)
    return jsonify({"status": "success"}), 200

@app.route('/api/get_queries', methods=['GET'])
def get_queries():
    return jsonify(load_queries()), 200

@app.route('/api/get_documents', methods=['GET'])
def get_documents():
    return jsonify(load_uploaded_documents()), 200

@app.route('/api/log_feedback', methods=['POST'])
def log_feedback():
    data = request.json
    valid_ratings = ['thumbs_up', 'thumbs_down']
    
    try:
        rating = data.get('rating', '').lower()
        if rating not in valid_ratings:
            return jsonify({"error": "Invalid rating type"}), 400

        with open(FEEDBACK_DB, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                data.get('query', '').strip(),
                data.get('response', '').strip(),
                rating,
                data.get('comments', '').strip()
            ])
        return jsonify({"status": "feedback recorded"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test')
def test():
    return jsonify({"message": "Test successful"}), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)