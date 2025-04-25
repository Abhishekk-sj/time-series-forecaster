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

        # >>>>>> PAY EXTREME ATTENTION TO INDENTATION ON THIS 'try:' BLOCK <<<<<<
        # The 'try:' line must be indented correctly within the 'if file and file.filename.endswith('.csv'):' block.
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

        # >>>>>> PAY EXTREME ATTENTION TO INDENTATION ON THIS 'except:' LINE <<<<<<
        # The 'except Exception as e:' line must align EXACTLY with its paired 'try:' above it.
        except Exception as e:
            # Catch potential errors during file saving (e.g., permissions, disk full - though less likely on Render ephemeral storage)
            print(f"Error saving file: {e}")
            return jsonify({"error": "Failed to process file on server.", "details": str(e)}), 500

    else:
        # Handle cases where the uploaded file does not have a .csv extension
        print(f"Invalid file type uploaded: {file.filename}")
        return jsonify({"error": "Invalid file type. Please upload a CSV file."}), 400


# --- Frontend Serving Routes ---

# Basic / route (should ideally be hit only if static file serving fails)
# Keeping this here but the serve_root_index should take precedence if defined after it
def index():
    """Basic route to confirm backend is running."""
    print("--- HITTING BASIC INDEX ROUTE (Frontend Not Served) ---") # More specific debug log
    return "Time Series Forecaster Backend is Running! Navigate to the frontend URL."


# Dedicated route for the root path '/' to serve index.html
# PLACE THIS FUNCTION AND ITS DECORATOR *AFTER* the basic index() function
@app.route('/')
def serve_root_index():
    """Serve index.html for the root path."""
    # --- This should be hit if this route definition is evaluated last for '/' ---
    print("--- ENTERING SERVE ROOT INDEX FUNCTION ---") # Debug log
    # -------------------------------------------------

    # The path to index.html within the static folder
    index_html_path = os.path.join(app.static_folder, 'index.html')
    print(f"Root path requested. Trying to serve index.html from: {index_html_path}")

    # Check if the index.html file exists in the built static folder
    if os.path.exists(index_html_path):
         print("index.html found at expected static path for root!")
         # Use send_from_directory to safely serve the index.html file.
         # The second argument 'index.html' is the filename relative to the static_folder.
         return send_from_directory(app.static_folder, 'index.html')
    else:
         # If index.html is not found, the frontend build likely failed
         print("index.html NOT found at the expected static folder path for root.")
         return "Frontend not built or configured correctly (index.html missing at root)", 404


# Catch-all route for all OTHER paths (<path:path>)
# This route will handle requests for /static/..., /forecast, etc., but NOT the root /
# Keep this function definition *after* both '/' routes if possible, or at least after serve_root_index.
@app.route('/<path:path>')
def serve_static_files(path):
    """
    Serve static files from the frontend build directory for non-root paths.
    """
    print("--- ENTERING SERVE STATIC FILES FUNCTION (Non-Root) ---") # Debug log
    print(f"Attempting to serve path: /{path}")

    # Construct the full path to the requested file within the static folder directory
    requested_file = os.path.join(app.static_folder, path)
    print(f"Constructed requested file path: {requested_file}")

    # Basic security check (similar to before)
    try:
        static_folder_abs = os.path.abspath(app.static_folder)
        requested_file_abs = os.path.abspath(requested_file)
        if not requested_file_abs.startswith(static_folder_abs):
             print(f"Security check failed: {requested_file_abs} is not in {static_folder_abs}")
             return "Forbidden", 403
    except Exception as e:
            print(f"Error during path normalization/check: {e}")
            return "Internal Server Error during path check", 500

    # Check if the specific requested file exists within the static folder.
    if os.path.exists(requested_file):
         print(f"Serving static file: {requested_file}")
         return send_from_directory(app.static_folder, path)
    else:
        # If the specific file was not found, it's likely a client-side route.
        # Serve index.html as a fallback for client-side routing.
        print(f"Requested file not found: {requested_file}. Falling back to serving index.html for client-side routing.")
        index_html_path = os.path.join(app.static_folder, 'index.html')
        if os.path.exists(index_html_path):
             print("index.html found for fallback!")
             return send_from_directory(app.static_folder, 'index.html')
         # Pay close attention to indentation here!
        else:
              print("index.html NOT found even for fallback.")
              return "Resource not found and fallback index.html is missing", 404


# This block is primarily for running the Flask development server locally.
# Render's production environment uses a WSGI server like Gunicorn (configured in the Start Command)
# and will ignore this __main__ block.
if __name__ == '__main__':
    print("Running Flask app locally (development mode)")
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
