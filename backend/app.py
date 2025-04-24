# backend/app.py
from flask import Flask, request, jsonify, send_from_directory # Import send_from_directory
import os
from flask_cors import CORS

app = Flask(__name__, static_folder='../frontend/build') # Configure static folder relative to backend/

# WARNING: Allows ALL origins during development. Restrict in production.
CORS(app)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB

# ... (keep the /upload and /health routes as they are) ...

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve static files from the frontend build directory."""
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        # Serve index.html for the root and any other path
        # This is important for client-side routing in React
        return send_from_directory(app.static_folder, 'index.html')

# This block is mainly for local development setup if needed.
if __name__ == '__main__':
    print("Running Flask app locally (development mode)")
    # When running locally for frontend dev, you might run React dev server separately
    # and proxy requests to Flask. This local run config serves the *built* frontend.
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
