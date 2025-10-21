import os
import requests
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
load_dotenv(override=True)

class Embedder():
    def __init__(self, region, embed_batch_size=16):
        self.embedding_service_url = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:6000")
        self.region = region
        self.collection = "chromadb_" + region
        self.collection_name = region + "_embeddings"
        self.embed_batch_size = embed_batch_size
        self.client = None

    def get_chromadb_client(self, region, collection):

        # Get the absolute path to the chroma db
        current_dir = os.path.dirname(os.path.abspath(__file__))
        chroma_path = os.path.join(
            current_dir, "..", "..", "chroma", region, collection
        )
        chroma_client = chromadb.PersistentClient(path=chroma_path)
        return chroma_client

    def delete_chromadb_collection(self, collection_name):
        if self.client is None:
            self.client = self.get_chromadb_client(self.region, self.collection)
        try:
            self.client.delete_collection(name=collection_name)
            print(f"Collection {collection_name} deleted.")
        except Exception as e:
            print(e)

    def get_text_splitter(self, chunk_size=1000, chunk_overlap=200):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True
        )
        return text_splitter


    def embed_texts(self, texts):
        url = f"{self.embedding_service_url}/embed"
        all_embeddings = []

        for i in range(0, len(texts), self.embed_batch_size):
            batch_texts = texts[i:i + self.embed_batch_size]
            payload = {"texts": batch_texts, "batch_size": len(batch_texts)}
            try:
                response = requests.post(url, json=payload, timeout=45)
                response.raise_for_status()
                data = response.json()
                all_embeddings.extend(data["embeddings"])
            except (requests.RequestException, ValueError) as exc:
                raise RuntimeError(f"Failed to query embedding service for batch {i}-{i+len(batch_texts)}: {exc}") from exc
        return all_embeddings
    
    def query_texts(self, texts, region, n_results=5):
        url = f"{self.embedding_service_url}/query"
        payload = {
            "query_texts": texts,
            "region": region,
            "n_results": n_results
        }
        try:
            response = requests.post(url, json=payload, timeout=45)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise RuntimeError(f"Failed to query embedding service: {exc}") from exc
        return data
    
    def embed_and_add_documents(self, documents):
        """doc = { 
                    "content": text,
                    "metadata": row.to_dict(),
                    "key" : key
                }"""
        if self.client is None:
            self.client = self.get_chromadb_client(self.region, self.collection)

        collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=None,
        )
        text_splitter = self.get_text_splitter()
        for doc in documents:
            text = doc["content"]
            metadata = doc["metadata"]
            key = doc["key"]
            metadata.update({"jurisdiction": self.region})
            try:
                chunks = text_splitter.split_text(text)
                texts = [chunk for chunk in chunks]
                embeddings = self.embed_texts(texts)
                # print(texts)
                collection.add(
                    documents=texts,
                    metadatas=[metadata for _ in range(len(texts))],
                    embeddings=embeddings,
                    ids=[f"{key}_{i}" for i in range(len(texts))]
                )
            except Exception as e:
                print(f"Error embedding document {key}:", e)
                raise
        print("Finish batch")
        return collection


if __name__ == "__main__":
    region="eu"
    embedder = Embedder(region=region)
    embedder.delete_chromadb_collection(region+"_embeddings")
    doc = { 
        "content": """THE EUROPEAN PARLIAMENT AND THE COUNCIL OF THE EUROPEAN UNION,

Having regard to the Treaty on the Functioning of the European Union, and in particular Article 114 thereof,

Having regard to the proposal from the European Commission,

After transmission of the draft legislative act to the national parliaments,

Having regard to the opinion of the European Central Bank (1),

Having regard to the opinion of the European Economic and Social Committee (2),

Acting in accordance with the ordinary legislative procedure (3),

Whereas:

(1)

The creation of an integrated market for electronic payments in euro, with no distinction between national and cross-border payments is necessary for the proper functioning of the internal market. To that end, the single euro payments area (SEPA) project aims to develop common Union-wide payment services to replace current national payment services. As a result of the introduction of open, common payment standards, rules and practices, and through integrated payment processing, SEPA should provide Union citizens and businesses with secure, competitively priced, user-friendly, and reliable payment services in euro. This should apply to SEPA payments within and across national boundaries under the same basic conditions and in accordance with the same rights and obligations, regardless of location within the Union. SEPA should be completed in a way that facilitates access for new market entrants and the development of new products, and creates favourable conditions for increased competition in payment services and for the unhindered development and swift, Union-wide implementation of innovations relating to payments. Consequently, improved economies of scale, increased operating efficiency and strengthened competition should lead to downward price pressure in electronic payment services in euro on a ‘best-of-breed’ basis. The effects of this should be significant, in particular in Member States where payments are relatively expensive compared to other Member States. The transition to SEPA should therefore not be accompanied by overall price increases for payment service users (PSUs) in general and for consumers in particular. Instead, where the PSU is a consumer, the principle of not levying higher charges should be encouraged. The Commission will continue to monitor price developments in the payment sector and is invited to provide an annual analysis thereof.""",
        "metadata": {"published_date": "2020-01-31"},
        "key" : "key"
    }
    documents = [doc]
    collection = embedder.embed_and_add_documents(documents)
    results = embedder.query_texts(["What is the SEPA project?"], region, n_results=2)
    print(results)
