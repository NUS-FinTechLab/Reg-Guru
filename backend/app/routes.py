from flask import Blueprint, request, jsonify
from datetime import datetime
from .utils import (
    process_chat_query, log_feedback
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

@api.route('/chat', methods=['POST'])
def chat():
    """Handle chat queries using the RAG system."""
    data = request.json
    print("Received data:", data) 
    user_message = data.get("message", {}).get("text", "").strip()
    region = data.get("region", "us").lower()  # Default to US if no region specified
    
    # Validate region
    valid_regions = ['us', 'eu', 'sg']
    if region not in valid_regions:
        return jsonify({"error": f"Invalid region '{region}'. Must be one of: {valid_regions}"}), 400
    
    try:
        response = process_chat_query(user_message, region)
        return jsonify({"response": response}), 200
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
        log_feedback(
            query=data.get('query', ''),
            response=data.get('response', ''),
            rating=data.get('rating', ''),
            comments=data.get('comments', '')
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