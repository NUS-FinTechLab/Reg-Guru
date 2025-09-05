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

2. Install dependencies and start the server:
   ```
   pip install -r requirements.txt
   python app.py
   ```

### Frontend
1. In a separate terminal, install Node.js dependencies:
   ```
   npm install
   ```

2. (Optional) If on mac, run:
   ```
   export NODE_OPTIONS=--openssl-legacy-provider
   ```

3. Start the development server:
   ```
   npm run dev
   ```