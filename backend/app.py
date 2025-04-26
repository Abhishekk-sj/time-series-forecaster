# backend/app.py
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd # Import pandas

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
    # We keep this for the potential temporary save if direct read fails,
    # but the primary path will now read directly.
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
         os.makedirs(app.config['UPLOAD_FOLDER'])
         print(f"Created upload folder: {app.config['UPLOAD_FOLDER']}")

    # Check if the POST request has the file part with the key 'file'
    if 'file' not in request.files:
        print("No 'file' part in request.files")
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file'] # 'file' is a FileStorage object from Werkzeug
    print(f"Received file: {file.filename}")

    # If the user does not select a file, the browser submits an empty file without a filename.
    if file.filename == '':
        print("No selected file filename")
        return jsonify({"error": "No selected file"}), 400

    # Basic check for file extension
    if file and file.filename.endswith('.csv'):
        # --- Debug print before assigning filename ---
        print("File is CSV, attempting to assign filename variable...")

        # >>>>> THIS LINE WAS MISSING OR MISPLACED <<<<<
        filename = file.filename # This line assigns the filename variable!
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

        # --- Debug print after assigning filename ---
        print(f"Filename variable assigned: {filename}")

        # We will attempt to read headers directly from the file object first.
        # This filepath variable is primarily for a potential fallback save, not the main read path.
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename) # Path for potential temp save

        try:
            # >>>>> THIS IS THE MAIN LOGIC TO READ HEADERS <<<<<
            # Read the CSV file content directly from the FileStorage object into a pandas DataFrame
            # file is the FileStorage object from request.files['file']
            # nrows=0 reads only the header row, making it fast.
            # keep_default_na=False prevents pandas from interpreting 'NA' or empty strings as NaN in headers.
            df = pd.read_csv(file, nrows=0, keep_default_na=False)

            # Get the list of column names from the DataFrame's index (the columns)
            column_headers = df.columns.tolist()

            # --- Debug print after successful header extraction ---
            print(f"Extracted column headers: {column_headers}")

            # *** NOTE: We are NOT saving the file permanently here. ***
            # The file content was read directly from the request object.

            # Return a success response including the filename AND the column headers
            # filename variable should be defined at this point
            return jsonify({
                "message": "File uploaded successfully",
                "filename": filename,
                "column_headers": column_headers # Include the list of headers
            }), 200

        except Exception as e:
            # --- This block executes if an error occurs in the try block ---
            # Catch potential errors during file reading or processing with pandas
            # --- Debug print showing the exception object ---
            # This print should show the original exception caught by 'e'.
            print(f"Error reading or processing file with pandas. Exception object: {e}") # <-- This is the correct print

            # Return an error response to the frontend
            # We use str(e) to ensure the details key doesn't cause further NameErrors if e is complex.
            # filename variable might not be reliably available here if error was before assignment,
            # so avoid using 'filename' directly in this except block beyond basic print.
            return jsonify({"error": "Failed to read CSV headers.", "details": str(e)}), 500

    else:
        # --- This block handles cases where the file is NOT a CSV ---
        print(f"Invalid file type uploaded: {file.filename}")
        # filename variable is NOT defined in this else block, only file.filename
        return jsonify({"error": "Invalid file type. Please upload a CSV file."}), 400


@app.route('/forecast', methods=['POST'])
def run_forecast():
    """Receives file, column selections, and parameters, runs forecast."""
    print("Received request to /forecast") # Log server-side

    # Ensure the uploads folder exists (good practice)
    # This is where the file might be temporarily saved if needed, though we read directly.
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
         os.makedirs(app.config['UPLOAD_FOLDER'])
         print(f"Created upload folder: {app.config['UPLOAD_FOLDER']}")

    # 1. Get the file content (sent again from frontend)
    if 'file' not in request.files:
        print("No 'file' part in /forecast request.files")
        return jsonify({"error": "No file part in the request for forecasting"}), 400
    file = request.files['file']
    print(f"Received file for forecasting: {file.filename}")

    if file.filename == '':
         print("No selected file filename in /forecast")
         return jsonify({"error": "No selected file for forecasting"}), 400

    if not file.filename.endswith('.csv'):
         print(f"Invalid file type for forecasting: {file.filename}")
         return jsonify({"error": "Invalid file type for forecasting. Please upload a CSV file."}), 400


    # 2. Get the column selections and parameters from the JSON body
    # The frontend will send these in the request body, NOT as form data.
    # The file content is sent as multipart/form-data, JSON as application/json.
    # Flask's request.get_json() reads the JSON body.
    try:
        # Note: When sending multipart/form-data (the file) and application/json (the data)
        # in the same request, the JSON data is typically sent under a different
        # key in the multipart payload, or sometimes in a separate request.
        # A simpler approach for now is to send the selections/params as form fields
        # along with the file in a single multipart/form-data request, or send the file
        # then the JSON in a second request. Let's assume frontend sends JSON under 'data' key.
        # We'll refine this based on frontend implementation.
        # For now, let's read the form data which is sent with the file in multipart.
        selected_columns_json = request.form.get('selectedColumns') # Frontend will likely send as form field
        forecast_periods_str = request.form.get('forecastPeriods')   # Frontend will likely send as form field

        if not selected_columns_json or not forecast_periods_str:
             print("Missing selectedColumns or forecastPeriods in form data")
             return jsonify({"error": "Missing forecasting inputs in request."}), 400

        # Parse the JSON string for selected columns
        import json
        try:
            selected_columns = json.loads(selected_columns_json)
        except json.JSONDecodeError:
            print("Failed to parse selectedColumns JSON")
            return jsonify({"error": "Invalid format for column selections."}), 400


        print(f"Received selections (parsed): {selected_columns}")
        print(f"Received forecast periods (string): {forecast_periods_str}")


        # Basic check that required columns are present in the selections JSON
        if not selected_columns or not all(col in selected_columns for col in ['Date Column', 'Value Column']):
             print("Missing required column types in selections JSON")
             return jsonify({"error": "Missing required column selections (Date and Value). Please select both."}), 400

        # Basic check that forecastPeriods is a positive integer
        try:
            forecast_periods = int(forecast_periods_str)
            if forecast_periods <= 0:
                 print("Forecast periods must be positive")
                 return jsonify({"error": "Forecast periods must be a positive integer."}), 400
        except (ValueError, TypeError):
             print("Forecast periods is not a valid integer")
             return jsonify({"error": "Forecast periods must be a valid integer."}), 400

        # --- TODO: Add Data Processing and Forecasting Logic Here ---
        # - Read the full CSV data using the provided file object and selections
        # - Select relevant columns based on user input
        # - Perform any necessary data cleaning, aggregation (if aggregation column is provided)
        # - Convert date column to datetime objects
        # - Set date column as index
        # - Apply forecasting model (e.g., ARIMA, Prophet)
        # - Generate forecast for forecast_periods
        # - Format results (forecasted values, confidence intervals)
        # ------------------------------------------------------------

        # >>> IMPORTANT: Add this part later once we have the forecasting logic <<<
        # # Example of reading full data after validating inputs:
        # file.seek(0) # Reset file pointer to the beginning before reading the full data
        # df_full = pd.read_csv(file, keep_default_na=False)
        # print(f"Successfully read full data for forecasting. DataFrame shape: {df_full.shape}")

        # For now, just return a success message and the received inputs
        # Replace this with actual forecast results later
        print("Inputs received and file read successfully. Forecasting logic goes here.")
        return jsonify({
            "message": "Forecast request received and inputs processed",
            "filename": file.filename,
            "selectedColumns": selected_columns,
            "forecastPeriods": forecast_periods,
            # "data_rows_read": df_full.shape[0] # Add this after reading full data
            # TODO: Add actual forecast results here
        }), 200

    except Exception as e:
        # Catch errors during data reading or initial processing steps
        print(f"Error processing inputs or reading full data in /forecast: {e}")
        return jsonify({"error": "Failed to process forecasting request.", "details": str(e)}), 500

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
