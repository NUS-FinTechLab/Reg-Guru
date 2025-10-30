## Key Dependencies

- **ChromaDB** – Persistent vector store
- **Transformers / Sentence-Transformers** – Embedding models and text preprocessing utilities
- **PyTorch** – Backing framework for embeddings (with CUDA support if available)

---

## Push docker image to AWS Amazon Elastic Container Registry
1. Allow docker to push to AWS. Ensure AWS CLI v2 is installed in your environment. If no AWS credential has been filled up, run `aws configure` and fill in the credentials before running the following commands. 
```bash
aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin 586794457319.dkr.ecr.ap-southeast-1.amazonaws.com
```

2. Build or rebuild docker image
```bash
cd embedding_service
docker build -t project/reg-guru-embedding:latest
```

3. Tag the image with AWS ECR URI
Look for your Repository URI from Amazon ECR - Repositories. In this example, `URI = 586794457319.dkr.ecr.ap-southeast-1.amazonaws.com/project/reg-guru-embedding`. Tag the image with the URI and push.
```bash
docker tag project/reg-guru-embedding:latest 586794457319.dkr.ecr.ap-southeast-1.amazonaws.com/project/reg-guru-embedding:latest

docker push 586794457319.dkr.ecr.ap-southeast-1.amazonaws.com/project/reg-guru-embedding:latest
```
