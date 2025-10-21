import os
import shutil
from hashlib import md5
import json
from dataclasses import dataclass
from typing import Any, Dict, List

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from openai import OpenAI

from .config import (
    VECTORSTORE_DIRECTORY,
    TEMP_DIR,
    MODEL_NAME,
    MODEL_TEMPERATURE,
    RETRIEVAL_K,
    PROMPT_TEMPLATE,
    CHECKLIST_SYSTEM_PROMPT,
    CHECKLIST_USER_PROMPT_TEMPLATE,
    CHECKLIST_JSON_SCHEMA,
    CHECKLIST_DEFAULT_PROMPT,
    EMBEDDING_SERVICE_URL,
)
from .models import Chat, Feedback

# Initialize LLM components
llm = ChatOpenAI(model=MODEL_NAME, temperature=MODEL_TEMPERATURE)
embeddings = OpenAIEmbeddings()
prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
openai_client = OpenAI()

MAX_CONTEXT_SNIPPET_CHARS = 1600


@dataclass(frozen=True)
class ChecklistPromptTemplate:
    """Helper for assembling checklist prompts with consistent sections."""

    template: str

    def render(
        self,
        *,
        mission: str,
        user_context: str,
        region: str,
        user_prompt: str,
        retrieved_context: str,
    ) -> str:
        return self.template.format(
            mission=self._clean_text(mission, "Not provided."),
            user_context=self._clean_text(user_context, "Not provided."),
            region=self._clean_text(region, "Not specified"),
            user_prompt=self._clean_text(
                user_prompt,
                "Provide a compliance checklist aligned with the mission.",
            ),
            retrieved_context=self._clean_text(
                retrieved_context,
                "No retrieved regulatory passages available.",
            ),
        ).strip()

    @staticmethod
    def _clean_text(value: str, fallback: str) -> str:
        value = (value or "").strip()
        return value if value else fallback


checklist_prompt_template = ChecklistPromptTemplate(CHECKLIST_USER_PROMPT_TEMPLATE)

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
    chat_id: str,
    rating: str,
    comments: str = "",
    message_id: int | None = None,
):
    """Write feedback records to PostgreSQL."""

    valid_ratings = {"thumbs_up", "thumbs_down"}
    rating_normalized = rating.lower().strip()

    if rating_normalized not in valid_ratings:
        raise ValueError("Invalid rating type")

    chat = Chat.get_by_id(chat_id)
    if chat is None:
        raise ValueError("Unknown chat")

    Feedback.create(
        chat_id=chat.id,
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


def generate_checklist_draft(
    prompt_text: str,
    region: str,
    *,
    mission: str,
    context: str,
) -> Dict[str, Any]:
    """Generate a structured checklist draft using embeddings and OpenAI JSON mode."""

    prompt_clean = (prompt_text or "").strip() or CHECKLIST_DEFAULT_PROMPT

    mission_clean = (mission or "").strip()
    context_clean = (context or "").strip()

    combined_query_parts = [mission_clean, context_clean, prompt_clean]
    combined_query = " \n".join(part for part in combined_query_parts if part)
    documents: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    distances: List[Any] = []

    if combined_query:
        try:
            query_results = _query_embedding_service(
                [combined_query], region, RETRIEVAL_K
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            raise RuntimeError(
                f"Failed to query embedding service for checklist generation: {exc}"
            ) from exc

        raw_documents = query_results.get("documents") or []
        if raw_documents and isinstance(raw_documents, list):
            documents = raw_documents[0] or []

        raw_metadatas = query_results.get("metadatas") or []
        if raw_metadatas and isinstance(raw_metadatas, list):
            metadatas = raw_metadatas[0] or []

        raw_distances = query_results.get("distances") or []
        if raw_distances and isinstance(raw_distances, list):
            distances = raw_distances[0] or []

    context_sections: List[str] = []
    sources: List[Dict[str, Any]] = []

    for index, document in enumerate(documents):
        if not isinstance(document, str):
            continue

        snippet = document.strip()
        if not snippet:
            continue
        if len(snippet) > MAX_CONTEXT_SNIPPET_CHARS:
            snippet = f"{snippet[:MAX_CONTEXT_SNIPPET_CHARS].rstrip()}..."

        metadata = {}
        if index < len(metadatas) and isinstance(metadatas[index], dict):
            metadata = metadatas[index]

        distance_value = None
        if index < len(distances):
            try:
                distance_value = float(distances[index])
            except (TypeError, ValueError):
                distance_value = None

        title = str(metadata.get("title") or f"Document {index + 1}")
        link = metadata.get("link") or metadata.get("url")

        section_lines = [f"Title: {title}"]
        if link:
            section_lines.append(f"Link: {link}")
        if distance_value is not None:
            section_lines.append(f"Similarity: {distance_value}")
        section_lines.append("Content:")
        section_lines.append(snippet)
        context_sections.append("<document> \n")
        context_sections.append("Document Title:" + title + "\n")
        context_sections.append("Document Link:" + (link or "N/A") + "\n")
        context_sections.append(title + "'s Content:\n")
        context_sections.append("\n".join(section_lines))
        context_sections.append("</document> \n")  # Blank line between sections

        filtered_metadata: Dict[str, Any] = {}
        for key, value in metadata.items():
            if key in {"chunk", "content", "text"}:
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                filtered_metadata[key] = value
            else:
                filtered_metadata[key] = str(value)

        sources.append(
            {
                "title": title,
                "link": link,
                "distance": distance_value,
                "metadata": filtered_metadata,
            }
        )

    if not context_sections:
        context_sections.append(
            "No relevant regulatory documents were retrieved for this request. Provide"
            " pragmatic best-practice guidance and flag missing citations."
        )

    retrieved_context = "\n\n".join(context_sections)

    region_label = (region or "").strip().upper() or "N/A"

    user_message = checklist_prompt_template.render(
        mission=mission_clean,
        user_context=context_clean,
        region=region_label,
        user_prompt=prompt_clean,
        retrieved_context=retrieved_context,
    )

    messages = [
        {"role": "system", "content": CHECKLIST_SYSTEM_PROMPT.strip()},
        {"role": "user", "content": user_message},
    ]

    try:
        completion = openai_client.chat.completions.create(
            model=MODEL_NAME,
            temperature=MODEL_TEMPERATURE,
            response_format={
                "type": "json_schema",
                "json_schema": CHECKLIST_JSON_SCHEMA,
            },
            messages=messages,
        )
    except Exception as exc:  # pragma: no cover - network failure path
        raise RuntimeError(f"OpenAI checklist generation failed: {exc}") from exc

    choices = getattr(completion, "choices", None) or []
    if not choices:
        raise RuntimeError("OpenAI returned no choices for checklist generation")

    content = (
        getattr(choices[0].message, "content", None) if choices[0].message else None
    )
    if not content:
        raise RuntimeError("OpenAI returned empty content for checklist generation")

    try:
        parsed_payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("OpenAI response was not valid JSON") from exc

    if not isinstance(parsed_payload, dict):
        raise RuntimeError("Checklist generation response must be a JSON object")

    return {
        "checklist": parsed_payload,
        "sources": sources,
        "metadata": {
            "region": region,
            "mission": mission_clean,
            "context": context_clean,
            "prompt": prompt_clean,
            "retrievedDocumentCount": len(sources),
            "retrievedContext": retrieved_context,
        },
    }
