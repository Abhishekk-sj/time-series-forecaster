# backend/app.py
import os
from flask import Flask, request, jsonify
from flask_cors import CORS # Import CORS

# Initialize Flask application
app = Flask(__name__)

# Enable CORS for all origins during development. Restrict this in production if needed.
CORS(app)

# Configuration for file uploads (directory will be ephemeral on Render)
UPLOAD_FOLDER = 'uploads'
# Ensure the upload directory exists on startup
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # Limit file size to 16MB

# Basic route to confirm backend is running
@app.route('/')
def index():
    return "Time Series Forecaster Backend is Running! (Initial Version)"

# Health check endpoint - useful for Render
@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "message": "Backend is alive!"}), 200

# Placeholder route for file upload (minimal implementation for initial deploy)
@app.route('/upload', methods=['POST'])
def upload_file():
     # In this initial version, we just confirm receipt
     print("Received request to /upload (Initial Version)")
     if 'file' not in request.files:
          return jsonify({"error": "No file part"}), 400
     file = request.files['file']
     return jsonify({"message": f"Received file: {file.filename} (Initial Version)"}), 200


# This block is primarily for running the Flask development server locally.
# Render's production environment uses Gunicorn (configured in the Start Command)
# and will ignore this __main__ block.
if __name__ == '__main__':
    print("Running Flask app locally (development mode)")
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
