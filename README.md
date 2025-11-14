# Reg-Guru: An RAG-enhanced Compliance Assistant
This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Reference Links
S3 connection
> https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html

RDS connection
> https://pypi.org/project/psycopg2/

## Development Setup
The project consists of a few components, including a web app which user interacts with and a few data ingestion pipelines to be scheduled to keep the vector store up-to-date. **Both the web app and pipelines reply on a long-run embedding service.** `backend`, `frontend`, `data_ingestion` and `service` serve as Git submodules in this mono repository. 

To clone the repositories correctly into \<your-mono-repo\>, run:

```bash
# Clone with submodules
git clone --recursive https://github.com/NUS-FinTechLab/Reg-Guru <your-mono-repo>
cd <your-mono-repo>

# [Optional] Update submodules if they already cloned without --recursive
git submodule update --init --recursive

# Checkout development branches (if needed)
git submodule foreach 'git checkout master'
```

To update them correctly:

1. Commit changes inside each submodules first. 
   ```bash
   cd <submodule>
   git status  # check what needs committing
   git add .
   git commit -m "<your-commit-message>"
   git push -u origin <branch>  # push to the submodule remote
   cd .. # go back to the mono repository
   ```
2. Update the mono repository to point to the latest submodule commits.
   ```bash
   git status
   ```
   You should see:
   ```
   modified: backend
   modified: data_ingestion
   modified: frontend
   modified: service
   ```
   Then, stage, commit, and push the mono repository.
   ```bash
   git add backend data_ingestion frontend service
   git commit -m "Update all submodules to latest commits"
   git push -u origin <branch>
   ```
3. Create pull requests inside each submodule if necessary before creating a pull request in the mono repository.
4. Or, you may automate committing & pushing process using `git submodule foreach` in the **mono repository**:
   ```bash
   git submodule foreach '
   git status --porcelain | grep -q . || exit 0
   echo "Committing changes in $name..."
   git add .
   git commit -m "Update submodules"
   git push --set-upstream origin <branch>
   '
   ```
   If submodules commit successfully, update the submodule references in the mono repository:
   ```bash
   git add .
   git commit -m 'Update submodule references'
   git push origin <branch>
   ```
   Run `git pull origin` inside the submodules before working on them individually.

5. To update the submodules to the latest commit by other developers on their branch directly:
   ```bash
   git submodule update --remote
   ```
   Then, update the submodule references in the mono repository as in step 4.
### 1. Backend

#### a. Setup
In `backend/`, create `.env` based on `.env.template`. The backend reuses the same PostgreSQL instance as the ingestion pipelines.

Create an environment for backend and activate it.

```bash
cd backend
pip install -r requirements.txt
# Or faster pip through Tsinghua mirrors: pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

python app.py # Start the server
```

#### b. ChromaDB
- Default host: `ec2-13-228-79-108.ap-southeast-1.compute.amazonaws.com`
- Default port: `80`
- Override with `CHROMADB_HOST` / `CHROMADB_PORT` if you need to point at a different deployment.
- Configure `CHROMADB_COLLECTION` to rename the shared collection (defaults to `reg_guru_embeddings`).
- If the deployment enforces auth, set `CHROMADB_AUTH_TOKEN` so runtime clients send the required Bearer header.
- SSH access (for maintenance only):
  - `ssh -i regguru-chromadb.pem ubuntu@ec2-13-228-79-108.ap-southeast-1.compute.amazonaws.com`

#### c. Chat & Feedback Persistence
- Chats, messages, and feedback now live in PostgreSQL (schema `app`).
- The backend reads the same credentials defined for the ingestion pipelines; no additional secrets are required.
- REST endpoints:
- `GET /api/chats` lists conversations for the authenticated user.
- `POST /api/chat` accepts `chatId`, `message.text`, and `region`; responses include stored message metadata.
- `GET /api/chat/<chatId>` returns the persisted conversation history.
- `POST /api/log_feedback` stores per-message feedback tied to the chat session.
- Use the migration helper whenever SQL files change in `backend/migrations/` (see the workflow below).

#### d. Database Migration Workflow
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

### 2. Embedding Service
An isolated, long-run embedding service allows a smoother experience in switching embedding models and avoids contaminating the backend + data_ingestion environments. A FastAPI app wraps the embedding service and basic ChromaDB queries. **It can be run persistently and used in both document and query embedding.**

#### a. Setup
In `service/`, create `.env` based on `.env.template`. 

In a separate terminal, create an environment for service and activate it.
```bash
cd service
pip install -r requirements.txt
# Or faster pip through Tsinghua mirrors: pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

uvicorn embedding_service:app --host 0.0.0.0 --port 6000 --reload # Start the service
```

#### b. Environment variables:

- `EMBEDDING_MODEL` – Override the default `BAAI/bge-m3`.
- `EMBEDDING_SERVICE_URL` – Backend override (defaults to `http://localhost:6000`).
- `CHROMADB_HOST` – Remote Chroma endpoint (defaults to the shared EC2 instance).
- `CHROMADB_PORT` – Remote Chroma port (defaults to `80`).
- `CHROMADB_COLLECTION` – Shared collection name (defaults to `reg_guru_embeddings`).
- `CHROMADB_AUTH_TOKEN` – Optional Bearer token when the service requires authentication.

#### c. API endpoints:

- `POST /embed` – Returns dense embeddings for supplied texts.
- `POST /query` – Queries Chroma collections with specified filters.
- `GET /collections/{region}/count` – Retrieves document counts.

### 3. Frontend
In `frontend/`, create `.env` based on `.env.template`. 

In a separate terminal, create an environment for frontend and activate it.
```bash
cd frontend
npm install # Install Node.js dependencies
export NODE_OPTIONS=--openssl-legacy-provider # (Optional) If on mac, run

npm run dev # Start the development server
```

### 4. Data Ingestion
This is to build and maintain the central knowledge base, where a few pipelines can be scheduled to run regularly.

In `data_ingestion/`, create `.env` based on `.env.template`. 

In a separate terminal, create an environment for data_ingestion and activate it.
``` bash
cd data_ingestion
pip install -r requirements.txt
# Or faster pip through Tsinghua mirrors: pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```
Refer to data_ingestion/README.md to run the pipelines.