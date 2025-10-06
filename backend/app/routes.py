from flask import Blueprint, request, jsonify

from .utils import process_chat_query, log_feedback
from .storage import (
    get_session_by_external_id,
    get_session_by_id,
    list_messages,
    upsert_session,
    insert_message,
    insert_saved_query,
    list_saved_queries,
)

# Create Blueprint
api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    """Handle CORS preflight requests."""
    response = jsonify({'success': True})
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response

def _serialize_session(session_row):
    return {
        "id": session_row["id"],
        "chatId": session_row["external_id"],
        "region": session_row["region"],
        "createdAt": session_row["created_at"].isoformat(),
        "updatedAt": session_row["updated_at"].isoformat(),
    }


def _serialize_message(message_row):
    return {
        "id": message_row["id"],
        "role": message_row["role"],
        "text": message_row["body"],
        "sources": message_row["sources"],
        "timestamp": message_row["sent_at"].isoformat(),
    }


def _serialize_saved_query(record):
    data = dict(record)
    session_id = data.get("session_id")
    data["session_id"] = str(session_id) if session_id else None
    created_at = data.get("created_at")
    if created_at is not None:
        data["created_at"] = created_at.isoformat()
    return data


@api.route('/chat', methods=['POST'])
def chat():
    """Handle chat queries using the RAG system."""
    data = request.json
    print("Received data:", data)

    user_message = data.get("message", {}).get("text", "").strip()
    region = data.get("region", "us").lower()  # Default to US if no region specified
    chat_external_id = str(data.get("chatId") or data.get("chat_id") or "").strip()

    # Validate region
    valid_regions = ['us', 'eu', 'sg']
    if region not in valid_regions:
        return jsonify({"error": f"Invalid region '{region}'. Must be one of: {valid_regions}"}), 400

    if not chat_external_id:
        return jsonify({"error": "chatId is required"}), 400

    if not user_message:
        return jsonify({"error": "message text is required"}), 400

    try:
        session = upsert_session(chat_external_id, region)

        user_message_row = insert_message(
            session_id=session["id"],
            role="user",
            body=user_message,
            sources=[],
        )

        result = process_chat_query(user_message, region)
        if isinstance(result, tuple):
            response, sources = result
        else:
            response = result
            sources = {'sources': []}

        source_list = sources.get('sources', [])

        bot_message_row = insert_message(
            session_id=session["id"],
            role="bot",
            body=response,
            sources=source_list,
        )
        
        print("Sources:", sources)
        return jsonify({
            "response": response,
            "sources": source_list,
            "session": _serialize_session(session),
            "messages": {
                "user": _serialize_message(user_message_row),
                "bot": _serialize_message(bot_message_row),
            },
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"Error during query processing: {str(e)}")
        return jsonify({"error": f"Failed to process query: {str(e)}"}), 500

@api.route('/log_feedback', methods=['POST'])
def log_feedback_route():
    """Log user feedback."""
    data = request.json
    
    try:
        chat_external_id = str(data.get('chatId', '')).strip()
        if not chat_external_id:
            return jsonify({"error": "chatId is required"}), 400

        message_id = data.get('messageId')
        if message_id is not None:
            try:
                message_id = int(message_id)
            except (TypeError, ValueError):
                return jsonify({"error": "messageId must be numeric"}), 400

        log_feedback(
            chat_external_id=chat_external_id,
            rating=data.get('rating', ''),
            comments=data.get('comments', ''),
            message_id=message_id,
        )
        return jsonify({"status": "feedback recorded"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/test')
def test():
    """Test endpoint to verify API is working."""
    return jsonify({"message": "Test successful"}), 200


@api.route('/chat/<string:chat_external_id>', methods=['GET'])
def get_chat(chat_external_id: str):
    session = get_session_by_external_id(chat_external_id)
    if session is None:
        return jsonify({"error": "Chat session not found"}), 404

    messages = [_serialize_message(row) for row in list_messages(session["id"])]

    return jsonify({
        "session": _serialize_session(session),
        "messages": messages,
    }), 200


@api.route('/saved_queries', methods=['GET'])
def get_saved_queries_route():
    saved = [_serialize_saved_query(row) for row in list_saved_queries()]
    return jsonify({"savedQueries": saved}), 200


@api.route('/saved_queries', methods=['POST'])
def create_saved_query():
    data = request.json or {}
    session_external_id = data.get('chatId')
    query_text = (data.get('query') or '').strip()
    response_summary = (data.get('responseSummary') or '').strip() or None

    if not query_text:
        return jsonify({"error": "query is required"}), 400

    session_id = None
    if session_external_id:
        session = get_session_by_external_id(session_external_id)
        session_id = session["id"] if session else None

    record = insert_saved_query(session_id, query_text, response_summary)
    record_dict = _serialize_saved_query(record)

    chat_external_id = None
    session_ref = record_dict.get('session_id')
    if session_ref:
        session_row = get_session_by_id(session_ref)
        if session_row:
            chat_external_id = session_row["external_id"]

    record_dict["chat_external_id"] = chat_external_id
    return jsonify({"savedQuery": record_dict}), 201
