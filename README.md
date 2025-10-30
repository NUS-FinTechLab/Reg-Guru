This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Reference Links
S3 connection
> https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html

RDS connection
> https://pypi.org/project/psycopg2/

## Development Setup
The project consists of a few components, including a web app which user interacts with and a few data ingestion pipelines to be scheduled to keep the vector store up-to-date. **Both the web app and pipelines reply on a separate embedding service.** 

### 1. Backend
1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Copy the required environment variables (including `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, and optional `DB_SSLMODE`) into `backend/.env`. The backend reuses the same PostgreSQL instance as the ingestion pipeline.

3. Create an environment and install dependencies:
   ```
   pip install -r requirements.txt
   # Or faster pip through Tsinghua mirrors: pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

4. Start the server:
   ```
   python app.py
   ```

### 2. ChromaDB
- Default host: `ec2-13-228-79-108.ap-southeast-1.compute.amazonaws.com`
- Default port: `80`
- Override with `CHROMADB_HOST` / `CHROMADB_PORT` if you need to point at a different deployment.
- Configure `CHROMADB_COLLECTION` to rename the shared collection (defaults to `reg_guru_embeddings`).
- If the deployment enforces auth, set `CHROMADB_AUTH_TOKEN` so runtime clients send the required Bearer header.
- SSH access (for maintenance only):
  - `ssh -i regguru-chromadb.pem ubuntu@ec2-13-228-79-108.ap-southeast-1.compute.amazonaws.com`

### 3. Chat & Feedback Persistence
- Chats, messages, and feedback now live in PostgreSQL (schema `app`).
- The backend reads the same credentials defined for the ingestion pipelines; no additional secrets are required.
- REST endpoints:
- `GET /api/chats` lists conversations for the authenticated user.
- `POST /api/chat` accepts `chatId`, `message.text`, and `region`; responses include stored message metadata.
- `GET /api/chat/<chatId>` returns the persisted conversation history.
- `POST /api/log_feedback` stores per-message feedback tied to the chat session.
- Use the migration helper whenever SQL files change in `backend/migrations/` (see the workflow below).

#### Database Migration Workflow
1. Ensure PostgreSQL connection variables are exported (or stored in `backend/.env`):
   ```bash
   export DB_HOST=...
   export DB_PORT=...
   export DB_USER=...
   export DB_PASSWORD=...
   export DB_NAME=...
   # optional
   export DB_SSLMODE=require
   ```
2. From the repository root apply all pending migrations using the tooling of your choice. Every `*.sql` file in `backend/migrations` is ordered lexically, so you can run them in that sequence, e.g.:
   ```bash
   for file in backend/migrations/*.sql; do
       psql "$DB_NAME" < "$file"
   done
   ```
   (Replace `psql` with another client if preferred.)
3. To add schema changes, drop a new, incrementally numbered SQL file (for example `backend/migrations/002_add_indexes.sql`) and rerun your migration command.
   ```bash
   python scripts/apply_migrations.py

### 4. Embedding Service
A separate embedding service allows a smoother experience in switching embedding models and avoids contaminating the backend + data_ingestion environments. A FastAPI app wraps the embedding service and ChromaDB queries. **It can be run persistently and used in both document and query embedding.**

#### Environment variables:

- `EMBEDDER_MODEL` – Override the default `BAAI/bge-m3`.
- `CHROMADB_ROOT_DIR` – Custom location for Chroma persistence.
- `EMBEDDING_SERVICE_URL` – Backend override (defaults to `http://localhost:6000`).

#### API endpoints:

- `POST /embed` – Returns dense embeddings for supplied texts.
- `POST /query` – Queries Chroma collections with specified filters.
- `GET /collections/{region}/count` – Retrieves document counts.

#### Setup

1. In a separate terminal, navigate to the embedding_service directory:
   ```
   cd embedding_service
   ```

2. Create a separate environment which is for running the embedding service only.
   ```bash
   pip install -r requirements.txt
   # Or faster pip through Tsinghua mirrors: pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

3. Start the service:
   ```
   uvicorn embedding_service:app --host 0.0.0.0 --port 6000 --reload
   ```

### 5. Frontend
1. In a separate terminal, navigate to the frontend directory:
   ```
   cd frontend
   ```
2. Install Node.js dependencies:
   ```
   npm install
   ```

3. (Optional) If on mac, run:
   ```
   export NODE_OPTIONS=--openssl-legacy-provider
   ```

4. Start the development server:
   ```
   npm run dev
   ```

### 6. Data Ingestion
This is a separate section to build and maintain the central knowledge base, where a few pipelines can be scheduled to run regularly.
1. In a separate terminal, navigate to the data_ingestion directory:
   ```
   cd data_ingestion
   ```

2. Copy the required environment variables (including `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, and optional `DB_SSLMODE`) into `data_ingestion/.env`. The backend reuses the same PostgreSQL instance as the ingestion pipeline.

3. Create an environment and install the dependencies:
   ```bash
   pip install -r requirements.txt
   # Or faster pip through Tsinghua mirrors: pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

4. Run the pipelines. Refer to data_ingestion/README.md.