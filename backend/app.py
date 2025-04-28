# backend/app.py
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd # Import pandas
import json # Import json for parsing selections
import numpy as np # Import numpy
# Import necessary modules from statsmodels for ARIMA
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tools.eval_measures import rmse # For evaluation later
import warnings # To suppress warnings from statsmodels
# Suppress specific warnings from statsmodels (Optional but recommended to keep logs cleaner)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning) # Often related to pandas/statsmodels interaction

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


    # 2. Get the column selections and parameters from the form data
    try:
        selected_columns_json = request.form.get('selectedColumns')
        forecast_periods_str = request.form.get('forecastPeriods')

        if not selected_columns_json or not forecast_periods_str:
             print("Missing selectedColumns or forecastPeriods in form data")
             return jsonify({"error": "Missing forecasting inputs in request."}), 400

        # Parse the JSON string for selected columns
        try:
            selected_columns = json.loads(selected_columns_json)
            date_col = selected_columns.get('Date Column')
            value_col = selected_columns.get('Value Column')
            agg_col = selected_columns.get('Aggregation Column (Optional)') # Can be None or empty string

        except json.JSONDecodeError:
            print("Failed to parse selectedColumns JSON")
            return jsonify({"error": "Invalid format for column selections."}), 400

        print(f"Received selections (parsed): Date='{date_col}', Value='{value_col}', Aggregation='{agg_col}'")
        print(f"Received forecast periods (string): {forecast_periods_str}")

        # Basic check that required columns are selected
        if not date_col or not value_col:
             print("Missing required column selections (Date and Value)")
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

    except Exception as e:
        print(f"Error processing inputs from /forecast request: {e}")
        return jsonify({"error": "Failed to process forecasting request inputs.", "details": str(e)}), 400


    # >>>>> START OF DATA PROCESSING AND FORECASTING LOGIC <<<<<
    try:
        # Reset file pointer to the beginning before reading the full data
        file.seek(0)
        # Read the entire CSV data into a pandas DataFrame
        df = pd.read_csv(file, keep_default_na=False) # Read full data

        print(f"Successfully read data. DataFrame shape: {df.shape}")
        print(f"DataFrame columns: {df.columns.tolist()}")

        # Validate if the selected columns actually exist in the DataFrame
        required_cols = [date_col, value_col]
        if agg_col:
             required_cols.append(agg_col)

        for col in required_cols:
            if col not in df.columns:
                print(f"Selected column '{col}' not found in data.")
                return jsonify({"error": f"Selected column '{col}' not found in uploaded data."}), 400

        # Select only the relevant columns
        selected_df = df[required_cols].copy() # Use .copy() to avoid SettingWithCopyWarning

        # Convert date column to datetime objects
        try:
             selected_df[date_col] = pd.to_datetime(selected_df[date_col])
        except Exception as e:
             print(f"Error converting date column '{date_col}' to datetime: {e}")
             return jsonify({"error": f"Failed to convert date column '{date_col}' to datetime. Please ensure it's in a recognizable format.", "details": str(e)}), 400

        # Handle aggregation if aggregation column is provided
        if agg_col and agg_col in selected_df.columns:
             print(f"Aggregating data by Date and '{agg_col}'...")
             # Group by Date and Aggregation column, sum the value column
             aggregated_df = selected_df.groupby([date_col, agg_col])[value_col].sum().reset_index()
             print(f"Aggregation complete. Aggregated DataFrame shape: {aggregated_df.shape}")

             # Now, if we need a single time series, we typically aggregate *again* by just date.
             # Common approach for forecasting is to sum or average values across categories for each date.
             # Let's sum values across different categories for the same date for a single time series.
             print("Further aggregating by Date only to get a single time series...")
             ts_data = aggregated_df.groupby(date_col)[value_col].sum().reset_index()

             print(f"Final time series data shape: {ts_data.shape}")

        else:
             print("No aggregation column provided or found. Using raw date/value columns.")
             # If no aggregation column, just use the date and value columns directly
             ts_data = selected_df[[date_col, value_col]].copy()
             # If multiple entries per date exist without aggregation, this will cause issues for simple models.
             # A proper check or implicit aggregation (like sum by date) might be needed depending on expected data.
             # For simplicity with ARIMA, let's implicitly sum values for the same date if they exist, even without an agg_col.
             print("Implicitly summing values by Date to ensure a single time series frequency...")
             ts_data = ts_data.groupby(date_col)[value_col].sum().reset_index()


        # Rename columns to generic 'Date' and 'Value' for consistency
        ts_data = ts_data.rename(columns={date_col: 'Date', value_col: 'Value'})

        # Sort by Date and set Date as index
        ts_data = ts_data.sort_values('Date')
        ts_data = ts_data.set_index('Date')

        # Drop rows with NaN values in the Value column
        ts_data.dropna(inplace=True)

        # Ensure the index has a frequency if needed by the model (ARIMA can sometimes infer)
        # If not already inferred, try setting a frequency (e.g., 'D' for daily, 'MS' for monthly start)
        # This can be tricky and might require user input or inference logic later.
        # For now, let statsmodels try to infer. If it fails, it might raise an error.
        # Example: ts_data.index = pd.to_datetime(ts_data.index) # Ensure index is datetime
        # try:
        #     ts_data = ts_data.asfreq('D') # Attempt to set daily frequency, fills missing dates with NaN
        #     ts_data[value_col].fillna(method='ffill', inplace=True) # Or .fillna(0) etc.
        # except Exception as freq_e:
        #     print(f"Could not set frequency: {freq_e}")
            # Handle frequency issues or require specific data structure


        # --- Apply Forecasting Model (Basic ARIMA) ---
        # A simple ARIMA(5,1,0) model as a starting point.
        # Order (p, d, q) parameters need to be selected based on data properties (ACF/PACF, stationarity)
        # This is a simplified example. Proper model selection is complex.
        order = (5, 1, 0)
        print(f"Applying ARIMA model with order {order}")

        # Fit the ARIMA model
        # The 'enforce_stationarity=False' and 'enforce_invertibility=False' are often used
        # with auto_arima or when starting with parameters, might need adjustment.
        # Let's try without initially.
        try:
            # Ensure the value column is numeric
            ts_data['Value'] = pd.to_numeric(ts_data['Value'], errors='coerce')
            ts_data.dropna(inplace=True) # Drop rows where Value couldn't be converted

            if ts_data.empty:
                 return jsonify({"error": "Processed data is empty after cleaning."}), 400
            if ts_data.shape[0] < 10: # Basic check for enough data points
                 return jsonify({"error": "Not enough data points for forecasting. Need at least 10."}), 400


            model = ARIMA(ts_data['Value'], order=order)
            model_fit = model.fit()
            print("ARIMA model fitted successfully.")
            # print(model_fit.summary()) # Optional: print model summary in logs

            # Generate forecast
            # predict() gives in-sample predictions, forecast() gives out-of-sample
            # Use forecast() for future periods
            forecast_result = model_fit.forecast(steps=forecast_periods)
            # get_forecast() provides confidence intervals
            forecast_steps = model_fit.get_forecast(steps=forecast_periods)

            # Extract forecast values and confidence intervals
            forecast_values = forecast_steps.predicted_mean
            conf_int = forecast_steps.conf_int() # Returns DataFrame with lower and upper bounds

            # Create a date index for the forecast periods
            # Assuming the data is at a regular frequency (e.g., daily, monthly)
            # Get the last date from the training data
            last_date = ts_data.index[-1]
            # Infer the frequency (e.g., 'D', 'MS') - this can be tricky if index has no freq
            # If ts_data.index.freq is None, try guessing or require user input later.
            # A simple approach is to generate dates based on the assumed frequency (e.g., daily)
            # or just generate a sequence of dates relative to the last date.
            # Let's try inferring or assuming a frequency for simplicity now.
            try:
                 forecast_index = pd.date_range(start=last_date, periods=forecast_periods + 1, freq=ts_data.index.freq or pd.infer_freq(ts_data.index))[1:] # Exclude last training date
                 # If freq is None and infer_freq fails, this line will raise an error.
                 # A robust solution needs better frequency handling.
            except Exception as freq_gen_e:
                 print(f"Could not generate forecast date index. Frequency issue? {freq_gen_e}")
                 # Fallback: Generate simple dates relative to last date (e.g., daily assumed)
                 # This assumes daily data if frequency cannot be inferred.
                 print("Attempting date generation assuming daily frequency...")
                 forecast_index = pd.date_range(start=last_date, periods=forecast_periods + 1, freq='D')[1:] # Assume daily if freq is None


            # Combine forecast results into a list of dictionaries
            forecast_data = []
            for i in range(forecast_periods):
                 forecast_data.append({
                     "Date": forecast_index[i].strftime('%Y-%m-%d'), # Format date as string
                     "ForecastValue": forecast_values.iloc[i],
                     "LowerBound": conf_int.iloc[i, 0],
                     "UpperBound": conf_int.iloc[i, 1]
                 })

            print(f"Forecast generated for {forecast_periods} periods.")

            # Return the forecast results
            return jsonify({
                "message": "Forecast generated successfully",
                "filename": file.filename,
                "selectedColumns": selected_columns,
                "forecastPeriods": forecast_periods,
                "forecastResults": forecast_data # <--- Include the actual forecast data
            }), 200

        except Exception as e:
            print(f"Error during ARIMA model fitting or forecasting: {e}")
            # Catch errors specific to model fitting/forecasting
            return jsonify({"error": "Failed to run forecasting model.", "details": str(e)}), 500

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
