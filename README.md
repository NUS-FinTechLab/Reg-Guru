This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Reference Links
S3 connection
> https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html

RDS connection
> https://pypi.org/project/psycopg2/

## Development Setup

### Backend
1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Copy the required environment variables (including `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, and optional `DB_SSLMODE`) into `backend/.env`. The backend reuses the same PostgreSQL instance as the ingestion pipeline.

3. Install dependencies:
   ```
   pip install -r requirements.txt
   # Or faster pip through Tsinghua mirrors: pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

4. Start the server:
   ```
   python app.py
   ```

### Chat & Feedback Persistence
- Chat sessions, messages, feedback, and saved queries now live in PostgreSQL (schema `app`).
- The backend reads the same credentials defined for the ingestion pipelines; no additional secrets are required.
- REST endpoints:
  - `POST /api/chat` accepts `chatId`, `message.text`, and `region`; responses include stored message metadata.
  - `GET /api/chat/<chatId>` returns the persisted conversation history.
  - `POST /api/log_feedback` stores per-message feedback tied to the chat session.
  - `GET|POST /api/saved_queries` expose lightweight query bookmarking.
- Apply any new SQL files in `backend/migrations/` using your preferred database tooling; they are designed to run sequentially.

### Frontend
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
