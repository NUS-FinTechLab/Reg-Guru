import os
import shutil
from hashlib import md5
import json
from typing import List

import requests
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from apscheduler.schedulers.background import BackgroundScheduler

from .config import (
    VECTORSTORE_DIRECTORY,
    TEMP_DIR,
    MODEL_NAME,
    MODEL_TEMPERATURE,
    RETRIEVAL_K,
    PROMPT_TEMPLATE,
    EMBEDDING_SERVICE_URL,
)
from .storage import (
    get_session_by_external_id,
    insert_feedback,
)

# Initialize LLM components
llm = ChatOpenAI(model=MODEL_NAME, temperature=MODEL_TEMPERATURE)
embeddings = OpenAIEmbeddings()
prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

# Initialize backup scheduler
scheduler = BackgroundScheduler()


def get_file_hash(file_path):
    """Get MD5 hash of a file."""
    with open(file_path, "rb") as f:
        return md5(f.read()).hexdigest()


def cleanup_temp():
    """Clean up temporary files and shutdown scheduler."""
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    if scheduler.running:
        scheduler.shutdown()


def process_chat_query(user_message, region="us"):
    """Process chat query using ChromaDB for a specific region."""
    if not user_message.strip():
        raise ValueError("Empty message")

    try:
        if _get_collection_count(region) == 0:
            raise FileNotFoundError(f"No documents found in {region} region collection")

        # Query the collection for relevant documents
        results = _query_embedding_service([user_message], region, RETRIEVAL_K)

        # Extract documents and metadata from results
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        print("Results:", json.dumps(results, indent=4))

        if not documents:
            return (
                f"No relevant documents found for your query in the {region} region.",
                {"sources": []},
            )

        # Construct prompt with retrieved documents including titles
        context_parts = []
        for i, document in enumerate(documents):
            # Get the title from metadata if available
            title = "Untitled Document"
            if i < len(metadatas) and metadatas[i] and "title" in metadatas[i]:
                title = metadatas[i]["title"]

            context_parts.append(f"Document: {title}\nContent: {document}")

        context = "\n\n".join(context_parts)

        # Use the prompt template from config
        formatted_prompt = prompt.format(context=context, question=user_message)

        # Get response from LLM
        response = llm.invoke(formatted_prompt)

        # Extract source information for frontend display
        sources = []
        seen_links = set()  # To avoid duplicate links

        for metadata in metadatas:
            if metadata and "link" in metadata and "title" in metadata:
                link = metadata["link"]
                title = metadata["title"]
                # Only add unique links
                if link not in seen_links:
                    sources.append({"title": title, "link": link})
                    seen_links.add(link)

        # Return the response
        response_content = (
            response.content if hasattr(response, "content") else str(response)
        )
        return response_content, {"sources": sources}

    except Exception as e:
        print(f"Error processing query for region {region}: {str(e)}")
        raise Exception(f"Failed to process query for {region} region: {str(e)}")


def log_feedback(
    chat_external_id: str,
    rating: str,
    comments: str = "",
    message_id: int | None = None,
):
    """Write feedback records to PostgreSQL."""

    valid_ratings = {"thumbs_up", "thumbs_down"}
    rating_normalized = rating.lower().strip()

    if rating_normalized not in valid_ratings:
        raise ValueError("Invalid rating type")

    session = get_session_by_external_id(chat_external_id)
    if session is None:
        raise ValueError("Unknown chat session")

    insert_feedback(
        session_id=session["id"],
        rating=rating_normalized,
        comments=comments.strip(),
        message_id=message_id,
    )


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
        if _get_collection_count(region) == 0:
            print(f"No documents found in {region} region collection")
            return []

        results = _query_embedding_service([user_message], region, n_results)

        # Extract documents from results
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        # Combine documents with metadata for context
        relevant_docs = []
        for doc, metadata, distance in zip(documents, metadatas, distances):
            relevant_docs.append(
                {"content": doc, "metadata": metadata, "distance": distance}
            )

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
        # Build context with document titles
        context_parts = []
        for doc in all_docs[:RETRIEVAL_K]:
            # Get the title from metadata if available
            title = "Untitled Document"
            if doc.get("metadata") and "title" in doc["metadata"]:
                title = doc["metadata"]["title"]

            context_parts.append(f"Document: {title}\nContent: {doc['content']}")

        context = "\n\n".join(context_parts)

        # Use the prompt template from config
        formatted_prompt = prompt.format(context=context, question=user_message)

        try:
            response = llm.invoke(formatted_prompt)
            combined_response = (
                response.content if hasattr(response, "content") else str(response)
            )

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


def _embedding_service_base_url() -> str:
    url = (EMBEDDING_SERVICE_URL or "").strip()
    if not url:
        raise RuntimeError("EMBEDDING_SERVICE_URL is not configured")
    return url.rstrip("/")


def _query_embedding_service(query_texts: List[str], region: str, n_results: int):
    url = f"{_embedding_service_base_url()}/query"
    payload = {
        "query_texts": query_texts,
        "region": region,
        "n_results": n_results,
    }

    try:
        response = requests.post(url, json=payload, timeout=45)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError(f"Failed to query embedding service: {exc}") from exc

    return {
        "documents": data.get("documents", [[]]),
        "metadatas": data.get("metadatas", [[]]),
        "distances": data.get("distances", [[]]),
    }


def _get_collection_count(region: str) -> int:
    url = f"{_embedding_service_base_url()}/collections/{region}/count"

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError(f"Failed to fetch collection count: {exc}") from exc

    count = data.get("count")
    if isinstance(count, int):
        return count
    try:
        return int(count)
    except (TypeError, ValueError):
        return 0
