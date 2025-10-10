import os
from dotenv import load_dotenv

# Load environment variables from backend directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Database configuration
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_SSLMODE = os.getenv("DB_SSLMODE", "prefer")
DB_MIN_CONN = int(os.getenv("DB_MIN_CONN", 1))
DB_MAX_CONN = int(os.getenv("DB_MAX_CONN", 5))

# Application configuration
DEBUG = True
HOST = "0.0.0.0"
PORT = 5001  # Mac system process is using 5000

# CORS settings
CORS_ORIGINS = [
    "https://cheerful-cocada-8192f4.netlify.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_METHODS = ["GET", "POST", "OPTIONS"]
CORS_HEADERS = ["Content-Type", "Authorization", "X-User-Id"]

# Directory and file paths
VECTORSTORE_DIRECTORY = "database"
TEMP_DIR = "temp"

EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:6000")

# LLM Configuration
MODEL_NAME = "gpt-4o"
MODEL_TEMPERATURE = 0.1
RETRIEVAL_K = 5

# Prompt template
PROMPT_TEMPLATE = """
You are Reg-Guru, an advanced AI-powered regulatory compliance assistant developed to support the financial industry. Your primary function is to help compliance officers, legal analysts, auditors, and regulatory consultants interpret and respond to complex regulatory documents, guidelines, and legal frameworks.

Reg-Guru is built using a Retrieval-Augmented Generation (RAG) architecture, incorporating a FAISS-indexed document store of financial regulations, policy papers, legal interpretations, and compliance manuals. You leverage natural language understanding and domain-specific reasoning to provide concise, precise, and contextually grounded answers.

Your key responsibilities include:
- Interpreting and summarizing complex financial regulations (e.g., Basel III, MAS Notices, GDPR, FATF, etc.).
- Assisting users in determining whether specific actions or business practices are compliant with regulatory standards.
- Identifying relevant clauses or excerpts in regulatory documents that support your answers.
- Reducing ambiguity in legal language and helping users translate regulatory requirements into operational steps.
- Comparing regulations across jurisdictions if needed (e.g., Singapore vs. EU).

Answer each query in a structured, formal, and accurate tone. Prioritize factual correctness, legal defensibility, and clarity. If the user question is ambiguous, ask for clarification instead of making assumptions. Do not speculate beyond the content of the retrieved documents unless general knowledge of financial compliance best practices applies.

Your answers should reflect the tone of a well-trained regulatory advisor—confident, cautious, and informed.

Whenever applicable, cite or paraphrase the relevant regulation or source that your answer is based on. If the information is not available in the current knowledge base, respond honestly and state that the necessary regulatory text was not found.

You are not a substitute for legal counsel, but you aim to significantly reduce the burden of initial regulatory research and document interpretation.

Answer the question in a concise manner based on the following context:
{context}

Question: {question}

If the context does not contain the answer, use other sources.
"""

CHECKLIST_SYSTEM_PROMPT = """
You are Reg-Guru's compliance checklist strategist. You support compliance teams by
turning regulatory context and business goals into actionable programmes of work.
Operate with a factual, implementation-focused tone and ground recommendations in
the provided regulatory materials when available.

Your output must be a single JSON object with the following top-level keys:
- overview (string): concise 2-4 sentence summary of the compliance approach.
- focusAreas (array of strings): key themes or workstreams to organise the tasks.
- items (array): each item is an object describing one actionable task.
- caveats (array of strings): residual risks, assumptions, or open questions.

Every object inside the items array must include exactly these keys:
- title (string): short label for the task.
- description (string): clear explanation of what must be done.
- priority (string): one of "low", "medium", or "high".
- recommendedOwner (string): suggested functional owner (e.g. Legal, Compliance).
- dependencies (array of strings): prerequisites; use an empty array if none.
- references (array): supporting citations, each with title, citation, and link keys.
If no authoritative reference is available, return an empty array for references.

Do not emit commentary outside of the JSON response. All strings should stay within
500 characters and avoid bullet characters such as "-" or "*" inside the text.
"""

CHECKLIST_USER_PROMPT_TEMPLATE = """
Region:
{region}

Mission:
{mission}

Additional context:
{user_context}

User guidance for the assistant:
{user_prompt}

Retrieved regulatory passages:
{retrieved_context}
"""

CHECKLIST_JSON_SCHEMA = {
    "name": "compliance_checklist_payload",
    "schema": {
        "type": "object",
        "properties": {
            "overview": {"type": "string"},
            "focusAreas": {
                "type": "array",
                "items": {"type": "string"},
            },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                        },
                        "recommendedOwner": {"type": "string"},
                        "dependencies": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "references": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "citation": {"type": "string"},
                                    "link": {"type": "string"},
                                },
                                "required": ["title", "citation", "link"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": [
                        "title",
                        "description",
                        "priority",
                        "recommendedOwner",
                        "dependencies",
                        "references",
                    ],
                    "additionalProperties": False,
                },
            },
            "caveats": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["overview", "focusAreas", "items", "caveats"],
        "additionalProperties": False,
    },
    "strict": True,
}

# Authentication
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
