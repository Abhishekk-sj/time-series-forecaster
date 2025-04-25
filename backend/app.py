# backend/app.py
from flask import Flask, request, jsonify, send_from_directory
import os
from flask_cors import CORS

# 1. Initialize Flask app and CORS
app = Flask(__name__, static_folder='../frontend/build')
CORS(app) # WARNING: Allows ALL origins during development. Restrict in production.

# 2. Configuration for file uploads
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB

# 3. The /health route
@app.route('/health')
def health_check():
    """Health check endpoint for Render."""
    return jsonify({"status": "healthy", "message": "Backend is alive!"}), 200

# 4. The /upload route
@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles file upload from the frontend."""
    print("Received request to /upload") # Log server-side
    # ... (rest of your upload_file function code) ...
    # Ensure the uploads folder exists (good practice on ephemeral filesystems)
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
         os.makedirs(app.config['UPLOAD_FOLDER'])
         print(f"Created upload folder: {app.config['UPLOAD_FOLDER']}")

    if 'file' not in request.files:
        print("No 'file' part in request.files")
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    print(f"Received file: {file.filename}")

    if file.filename == '':
        print("No selected file filename")
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.csv'):
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(filepath)
            print(f"File saved temporarily to {filepath}")
            return jsonify({
                "message": "File uploaded successfully",
                "filename": filename,
                "server_temp_filepath": filepath
            }), 200
        except Exception as e:
            print(f"Error saving file: {e}")
            return jsonify({"error": "Failed to process file on server.", "details": str(e)}), 500
    else:
        print(f"Invalid file type uploaded: {file.filename}")
        return jsonify({"error": "Invalid file type. Please upload a CSV file."}), 400


# 5. The basic / route (ideally hit only if static serving fails or for direct backend check)
@app.route('/')
def index():
    """Basic route to confirm backend is running."""
    return "Time Series Forecaster Backend is Running! Navigate to the frontend URL."


# 6. LASTLY: The static file serving routes (should catch / and /<path:path> before index)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """
    Serve static files from the frontend build directory.
    """
    print(f"Attempting to serve path: /{path}") # Debug log
    print(f"Static folder configured as: {app.static_folder}") # Debug log

    requested_file = os.path.join(app.static_folder, path)
    print(f"Constructed requested file path: {requested_file}") # Debug log

    try:
        static_folder_abs = os.path.abspath(app.static_folder)
        requested_file_abs = os.path.abspath(requested_file)
        if not requested_file_abs.startswith(static_folder_abs):
             print(f"Security check failed: {requested_file_abs} is not in {static_folder_abs}")
             return "Forbidden", 403
    except Exception as e:
        print(f"Error during path normalization/check: {e}")
        return "Internal Server Error during path check", 500


    if path == "":
        index_html_path = os.path.join(app.static_folder, 'index.html')
        print(f"Root path requested. Trying to serve index.html from: {index_html_path}")
        if os.path.exists(index_html_path):
             print("index.html found at expected static path!")
             return send_from_directory(app.static_folder, 'index.html')
        else:
             print("index.html NOT found at the expected static folder path for root.")
             return "Frontend not built or configured correctly (index.html missing at root)", 404

    if os.path.exists(requested_file):
         print(f"Serving static file: {requested_file}")
         return send_from_directory(app.static_folder, path)
    else:
         print(f"Requested file not found: {requested_file}. Falling back to serving index.html for client-side routing.")
         index_html_path = os.path.join(app.static_folder, 'index.html')
         if os.path.exists(index_html_path):
              print("index.html found for fallback!")
              return send_from_directory(app.static_folder, 'index.html')
         else:
              print("index.html NOT found even for fallback.")
              return "Resource not found and fallback index.html is missing", 404


# This block is mainly for local development setup if needed.
# Render will ignore this and use the 'start command' (Gunicorn).
if __name__ == '__main__':
    print("Running Flask app locally (development mode)")
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
