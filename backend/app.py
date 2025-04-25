# backend/app.py
from flask import Flask, request, jsonify, send_from_directory
import os
from flask_cors import CORS

# Initialize Flask app, telling it where to find static files after frontend build
# '../frontend/build' is relative to the 'backend/' directory, which is Render's Root Directory
app = Flask(__name__, static_folder='../frontend/build')

# WARNING: Allows ALL origins during development. Restrict in production.
CORS(app)

# Configuration for file uploads
# IMPORTANT: The 'uploads' directory on Render is ephemeral.
UPLOAD_FOLDER = 'uploads'
# Ensure the upload directory exists on startup
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB

@app.route('/')
def index():
    """Basic route to confirm backend is running."""
    # This route might not be hit directly if the / or /<path:path> route serves static files first
    return "Time Series Forecaster Backend is Running! Navigate to the frontend URL."

@app.route('/health')
def health_check():
    """Health check endpoint for Render."""
    return jsonify({"status": "healthy", "message": "Backend is alive!"}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles file upload from the frontend."""
    print("Received request to /upload") # Log server-side

    # Ensure the uploads folder exists (good practice on ephemeral filesystems)
    # Although we won't rely on saving here in the long run
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
            # Temporarily save the file - won't persist on Render restarts
            file.save(filepath)
            print(f"File saved temporarily to {filepath}")

            # TODO: In the next phase, read file content from request.files['file']
            # here INSTEAD of saving to process headers.

            return jsonify({
                "message": "File uploaded successfully",
                "filename": filename,
                "server_temp_filepath": filepath # Indicate this is temporary
            }), 200
        except Exception as e:
            print(f"Error saving file: {e}")
            # This might catch errors related to the ephemeral filesystem
            return jsonify({"error": "Failed to process file on server.", "details": str(e)}), 500

    else:
        print(f"Invalid file type uploaded: {file.filename}")
        return jsonify({"error": "Invalid file type. Please upload a CSV file."}), 400


# Add the route(s) to serve the static frontend files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """
    Serve static files from the frontend build directory.
    This function tries to find a specific file first,
    and falls back to serving index.html for client-side routing.
    """
    print(f"Attempting to serve path: /{path}") # Debug log
    print(f"Static folder configured as: {app.static_folder}") # Debug log

    # Construct the full path to the requested file within the static folder
    # Note: os.path.join handles '/' and '\' appropriately for the OS
    requested_file = os.path.join(app.static_folder, path)
    print(f"Constructed requested file path: {requested_file}") # Debug log

    # Basic security check: Ensure the resolved path is actually inside the static folder
    try:
        static_folder_abs = os.path.abspath(app.static_folder)
        requested_file_abs = os.path.abspath(requested_file)
        # Ensure the requested path starts with the absolute path of the static folder
        if not requested_file_abs.startswith(static_folder_abs):
             print(f"Security check failed: {requested_file_abs} is not in {static_folder_abs}")
             return "Forbidden", 403 # Or handle as a 404/redirect
    except Exception as e:
        print(f"Error during path normalization/check: {e}")
        # Handle potential errors during path processing
        return "Internal Server Error during path check", 500


    # If the requested path is empty (''), it's the root URL (e.g., visiting the main domain)
    if path == "":
        # Try to serve the main index.html file for the root path
        index_html_path = os.path.join(app.static_folder, 'index.html')
        print(f"Root path requested. Trying to serve index.html from: {index_html_path}")
        # Check if the index.html file actually exists in the built static folder
        if os.path.exists(index_html_path):
             print("index.html found at expected static path!")
             # Use send_from_directory to serve index.html from the static folder root
             return send_from_directory(app.static_folder, 'index.html')
        else:
             # If index.html is not found for the root path, the frontend build likely failed
             print("index.html NOT found at the expected static folder path for root.")
             # Return a specific error indicating the frontend build issue
             return "Frontend not built or configured correctly (index.html missing at root)", 404

    # If the path is not empty, it's requesting a specific file (e.g., /static/css/main.css, /logo.png)
    # Check if the specific requested file exists within the static folder
    if os.path.exists(requested_file):
         print(f"Serving static file: {requested_file}")
         # Use send_from_directory to serve the specific file
         # The 'path' variable contains the requested sub-path relative to the static folder
         return send_from_directory(app.static_folder, path)
    else:
        # If the specific file doesn't exist, and it wasn't the root path,
        # it could be a route for client-side routing (like /forecast or /settings).
        # In this case, we serve index.html and let the frontend (React Router) handle the path.
        print(f"Requested file not found: {requested_file}. Falling back to serving index.html for client-side routing.")
        index_html_path = os.path.join(app.static_folder, 'index.html')
        # Check if index.html exists for the fallback
        if os.path.exists(index_html_path):
             print("index.html found for fallback!")
             return send_from_directory(app.static_folder, 'index.html')
        else:
             # This case means neither the specific file nor index.html was found
             print("index.html NOT found even for fallback.")
             return "Resource not found and fallback index.html is missing", 404 # Final 404


# This block is mainly for local development setup if needed.
# Render will ignore this and use the 'start command' (Gunicorn).
if __name__ == '__main__':
    print("Running Flask app locally (development mode)")
    # When running locally for frontend dev, you might run React dev server separately
    # and proxy requests to Flask. This local run config serves the *built* frontend.
    # Use a port from the environment variable if available, default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Listen on all interfaces '0.0.0.0' for accessibility
    app.run(debug=True, host='0.0.0.0', port=port)
