# backend/app.py
from flask import Flask, request, jsonify
import os
from flask_cors import CORS # Needed to allow frontend to make requests

# __name__ is special variable in Python
app = Flask(__name__)
# Allow requests from the frontend domain (we'll relax this for dev)
CORS(app) # WARNING: Allows ALL origins during development. Restrict in production.

# Configuration for file uploads
# IMPORTANT: The 'uploads' directory on Render is ephemeral.
# Files saved here will be lost when the container restarts.
# We'll process the file content directly from request.files in later steps,
# but saving temporarily helps verify the upload mechanism works.
UPLOAD_FOLDER = 'uploads'
# Ensure the upload directory exists on startup
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16MB

@app.route('/')
def index():
    """Basic route to confirm backend is running."""
    return "Time Series Forecaster Backend is Running! Navigate to the frontend URL."

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles file upload from the frontend."""
    print("Received request to /upload") # Log server-side

    # Ensure the uploads folder exists (good practice on ephemeral filesystems)
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
         os.makedirs(app.config['UPLOAD_FOLDER'])
         print(f"Created upload folder: {app.config['UPLOAD_FOLDER']}") # Log server-side


    # Check if the POST request has the file part
    if 'file' not in request.files:
        print("No 'file' part in request.files") # Log server-side
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    print(f"Received file: {file.filename}") # Log server-side


    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        print("No selected file filename") # Log server-side
        return jsonify({"error": "No selected file"}), 400

    # Check if the file is a CSV
    if file and file.filename.endswith('.csv'):
        # SECURITY NOTE: Sanitize filenames properly in production.
        # For now, we use the original name but won't rely on the saved file's persistence.
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            # Temporarily save the file. On Render, this is not persistent.
            # We will read the file content directly from `request.files['file']` later.
            file.save(filepath)
            print(f"File saved temporarily to {filepath}") # Log server-side

            # In the next phase, we will read the file content here to get headers.
            # For now, we just confirm successful upload.
            return jsonify({
                "message": "File uploaded successfully",
                "filename": filename,
                # Indicate that the filepath is temporary on the server
                "server_temp_filepath": filepath
            }), 200
        except Exception as e:
            print(f"Error saving file: {e}") # Log server-side
            return jsonify({"error": "Failed to save file on server.", "details": str(e)}), 500

    else:
        print(f"Invalid file type uploaded: {file.filename}") # Log server-side
        return jsonify({"error": "Invalid file type. Please upload a CSV file."}), 400

# Health check endpoint - useful for Render to check service status
@app.route('/health')
def health_check():
    """Health check endpoint for Render."""
    return jsonify({"status": "healthy", "message": "Backend is alive!"}), 200


# This block is mainly for local development setup if needed.
# Render will ignore this and use the 'start command' (Gunicorn).
if __name__ == '__main__':
    print("Running Flask app locally (development mode)")
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
