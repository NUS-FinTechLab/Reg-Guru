from flask import Flask
from flask_cors import CORS
import atexit
from app.config import DEBUG, HOST, PORT, CORS_ORIGINS, CORS_METHODS, CORS_HEADERS
from app.utils import initialize_directories, setup_scheduler, cleanup_temp
from app.routes import api

# Create Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": CORS_ORIGINS,
        "methods": CORS_METHODS,
        "allow_headers": CORS_HEADERS
    }
})

# Register blueprints
app.register_blueprint(api)

# Initialize application
initialize_directories()

# Register cleanup function
atexit.register(cleanup_temp)

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=DEBUG)