# backend/app.py
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Initialize Flask app, telling it where to find static files after frontend build
# '../frontend/build' is relative to the 'backend/' directory, which is Render's Root Directory
# This assumes your Render service's Root Directory is set to 'backend'
app = Flask(__name__, static_folder='../frontend/build')

# WARNING: Allows ALL origins during development. Restrict in production if needed.
# CORS allows your frontend running on a different domain/port to talk to your backend.
CORS(app)

# Configuration for file uploads
# IMPORTANT: The 'uploads' directory on Render's free tier is ephemeral.
# Files saved here will be lost when the container restarts or scales down.
# We'll use this for temporary checking during development, but processing
# should ideally read directly from request.files in later phases.
UPLOAD_FOLDER = 'uploads'
# Ensure the upload directory exists on startup
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # Limit file size to 16MB (adjust as needed)


# --- API Routes ---

# Health check endpoint - useful for Render to check service status
@app.route('/health')
def health_check():
    """Health check endpoint for Render."""
    print("Health check route hit") # Debug log
    return jsonify({"status": "healthy", "message": "Backend is alive!"}), 200

# Route to handle file uploads from the frontend
@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles file upload from the frontend."""
    print("Received request to /upload") # Log server-side

    # Ensure the uploads folder exists (good practice even for ephemeral filesystems)
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
         os.makedirs(app.config['UPLOAD_FOLDER'])
         print(f"Created upload folder: {app.config['UPLOAD_FOLDER']}")

    # Check if the POST request has the file part with the key 'file'
    if 'file' not in request.files:
        print("No 'file' part in request.files")
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    print(f"Received file: {file.filename}")

    # If the user does not select a file, the browser submits an empty file without a filename.
    if file.filename == '':
        print("No selected file filename")
        return jsonify({"error": "No selected file"}), 400

    # Basic check for file extension
    if file and file.filename.endswith('.csv'):
        # SECURITY NOTE: Sanitize filenames properly in production to prevent directory traversal.
        # For now, we use the original name but won't rely on the saved file's persistence.
        filename = file.filename
        # Construct the full path where the file will be temporarily saved
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            # Temporarily save the file to the ephemeral filesystem.
            # This file will likely be removed on container restarts.
            # In the next phase, we will process the file content directly from request.files['file']
            # using pandas, WITHOUT saving it to the filesystem first.
            file.save(filepath)
            print(f"File saved temporarily to {filepath}")

            # Return a success response including the filename
            return jsonify({
                "message": "File uploaded successfully",
                "filename": filename,
                # Include the temporary server path for debugging, but frontend shouldn't rely on it
                "server_temp_filepath": filepath
            }), 200

        except Exception as e:
            # Catch potential errors during file saving (e.g., permissions, disk full - though less likely on Render ephemeral storage)
            print(f"Error saving file: {e}")
            return jsonify({"error": "Failed to process file on server.", "details": str(e)}), 500

    else:
        # Handle cases where the uploaded file does not have a .csv extension
        print(f"Invalid file type uploaded: {file.filename}")
        return jsonify({"error": "Invalid file type. Please upload a CSV file."}), 400


# --- Frontend Serving Routes ---

# Basic / route (should ideally be hit only if the static file serving routes fail or are commented out)
@app.route('/')
def index():
    """Basic route to confirm backend is running."""
    print("Basic index route hit") # Debug log
    return "Time Series Forecaster Backend is Running! Navigate to the frontend URL."


# Catch-all route to serve static files from the frontend build directory
# This should be placed LAST among your routes that could match '/' or other paths,
# to ensure more specific API routes are matched first.
# This route matches the root URL ('/') by default and any other path ('/<path:path>').
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """
    Serve static files from the frontend build directory.
    This function tries to serve a specific file if it exists in the build directory.
    If the specific file is not found (e.g., for a client-side route like /forecast),
    it falls back to serving the main index.html file so the frontend router can handle it.
    """
    # --- This is the absolute first line executed when this route is matched ---
    # If you don't see this log in Render runtime logs, the route is not being matched.
    print("--- ENTERING SERVE FUNCTION ---")
    # ---------------------------------------------------------------------------

    print(f"Attempting to serve path: /{path}")
    # Print the configured static folder path (should be ../frontend/build relative to backend root)
    print(f"Static folder configured as: {app.static_folder}")

    # Construct the full path to the requested file within the static folder directory
    # os.path.join handles different operating system path separators ('/' or '\')
    requested_file = os.path.join(app.static_folder, path)
    print(f"Constructed requested file path: {requested_file}")

    # Basic security check: Ensure the constructed file path is actually located
    # inside the configured static folder to prevent directory traversal attacks.
    try:
        # Get the absolute path of the static folder
        static_folder_abs = os.path.abspath(app.static_folder)
        # Get the absolute path of the requested file
        requested_file_abs = os.path.abspath(requested_file)
        # Check if the absolute path of the requested file starts with the absolute path of the static folder
        if not requested_file_abs.startswith(static_folder_abs):
             print(f"Security check failed: {requested_file_abs} is not in {static_folder_abs}")
             # Return a Forbidden status if the path is outside the allowed static directory
             return "Forbidden", 403 # Or you could return a 404 if you prefer not to indicate structure
    except Exception as e:
        # Catch any potential errors during path normalization or comparison
        print(f"Error during path normalization/check: {e}")
        # Return an internal server error if path processing fails
        return "Internal Server Error during path check", 500


    # Case 1: The requested path is empty (''), meaning the user is accessing the root URL (e.g., https://your-app.onrender.com/)
    if path == "":
        # Try to serve the main index.html file located at the root of the built static folder
        index_html_path = os.path.join(app.static_folder, 'index.html')
        print(f"Root path requested. Trying to serve index.html from: {index_html_path}")
        # Check if the index.html file actually exists at this path
        if os.path.exists(index_html_path):
             print("index.html found at expected static path for root!")
             # Use send_from_directory to safely serve the index.html file.
             # The second argument 'index.html' is the filename relative to the static_folder.
             return send_from_directory(app.static_folder, 'index.html')
        else:
             # If index.html is not found for the root path, it usually means the frontend build failed or was not deployed correctly.
             print("index.html NOT found at the expected static folder path for root.")
             # Return a specific error indicating the likely cause.
             return "Frontend not built or configured correctly (index.html missing at root)", 404

    # Case 2: The requested path is not empty, meaning the user is requesting a specific file (e.g., /static/css/main.css, /logo.png)
    # Check if the specific requested file exists within the static folder.
    if os.path.exists(requested_file):
         print(f"Serving static file: {requested_file}")
         # Use send_from_directory to safely serve the requested file.
         # The second argument 'path' is the sub-path relative to the static_folder.
         return send_from_directory(app.static_folder, path)
    else:
        # Case 3: The specific file was not found. This often happens for client-side routes (e.g., /forecast, /settings)
        # where the frontend (React Router) is expected to handle the routing after index.html is loaded.
        print(f"Requested file not found: {requested_file}. Falling back to serving index.html for client-side routing.")
        # Try to serve the main index.html file as a fallback.
        index_html_path = os.path.join(app.static_folder, 'index.html')
        # Check if index.html exists for the fallback
        if os.path.exists(index_html_path):
             print("index.html found for fallback!")
             return send_from_directory(app.static_folder, 'index.html')
         # ---> >>>>>> PAY EXTREME ATTENTION TO INDENTATION ON THIS NEXT LINE <<<<<< <---
         # The 'else:' below must align *exactly* with the 'if os.path.exists(index_html_path):' above it.
         # It should be indented two levels in from the 'if path == "":' line.
         else: # <--- This is likely the line causing the IndentationError
              print("index.html NOT found even for fallback.")
              # Return a 404 error as the resource wasn't found and the fallback index.html is also missing.
              return "Resource not found and fallback index.html is missing", 404


# This block is primarily for running the Flask development server locally.
# Render's production environment uses a WSGI server like Gunicorn (configured in the Start Command)
# and will ignore this __main__ block.
if __name__ == '__main__':
    print("Running Flask app locally (development mode)")
    # Get the port from the environment variable provided by the system (like Render or local setup)
    # Default to 5000 if the PORT environment variable is not set.
    port = int(os.environ.get('PORT', 5000))
    # Run the Flask app, listening on all public interfaces ('0.0.0.0')
    # debug=True is helpful for local development to see errors immediately,
    # but should ideally be False in production. Render handles logging separately.
    app.run(debug=True, host='0.0.0.0', port=port)
