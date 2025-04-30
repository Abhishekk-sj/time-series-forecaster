# backend/app.py
import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import numpy as np
# Import necessary modules from statsmodels for ARIMA and ETS
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import SimpleExpSmoothing # Import Simple Exponential Smoothing
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tools.eval_measures import rmse # Import RMSE for evaluation
import warnings # To suppress warnings from statsmodels

# Suppress specific warnings from statsmodels and pandas
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message="The `freq` argument is deprecated") # For pandas future warning on freq

# Define a mapping for frontend frequency names to pandas frequency codes
# Assuming 'MS' for Month Start, 'QS' for Quarter Start, 'AS' for Year Start
FREQUENCY_MAP = {
    'Daily': 'D',
    'Weekly': 'W',
    'Monthly': 'MS',
    'Quarterly': 'QS',
    'Yearly': 'AS'
}

# Initialize Flask app, telling it where to find static files after frontend build
app = Flask(__name__, static_folder='../frontend/build')
CORS(app)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024


@app.route('/health')
def health_check():
    """Health check endpoint for Render."""
    print("Health check route hit")
    return jsonify({"status": "healthy", "message": "Backend is alive!"}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles file upload from the frontend, reads headers, returns headers."""
    print("Received request to /upload")

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
        print("File is CSV, attempting to process headers...")

        try:
            file.seek(0)
            df = pd.read_csv(file, nrows=0, keep_default_na=False)

            column_headers = df.columns.tolist()
            print(f"Extracted column headers: {column_headers}")

            return jsonify({
                "message": "File uploaded successfully",
                "filename": file.filename,
                "column_headers": column_headers
            }), 200

        except Exception as e:
            print(f"Error reading CSV headers. Exception object: {e}")
            return jsonify({"error": "Failed to read CSV headers.", "details": str(e)}), 500

    else:
        print(f"Invalid file type uploaded: {file.filename}")
        return jsonify({"error": "Invalid file type. Please upload a CSV file."}), 400


@app.route('/forecast', methods=['POST'])
def run_forecast():
    """Receives file, column selections, parameters, and frequency, runs forecast."""
    print("Received request to /forecast")

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
         os.makedirs(app.config['UPLOAD_FOLDER'])
         print(f"Created upload folder: {app.config['UPLOAD_FOLDER']}")

    if 'file' not in request.files:
        print("No 'file' part in request.files")
        return jsonify({"error": "No file part in the request for forecasting"}), 400
    file = request.files['file']
    print(f"Received file for forecasting: {file.filename}")

    if file.filename == '':
         print("No selected file filename in /forecast")
         return jsonify({"error": "No selected file for forecasting"}), 400

    if not file.filename.endswith('.csv'):
         print(f"Invalid file type for forecasting: {file.filename}")
         return jsonify({"error": "Invalid file type for forecasting. Please upload a CSV file."}), 500

    # --- Get inputs from form data ---
    try:
        selected_columns_json = request.form.get('selectedColumns')
        selected_frequency_name = request.form.get('selectedFrequency')
        forecast_periods_str = request.form.get('forecastPeriods')

        if not selected_columns_json or not selected_frequency_name or not forecast_periods_str:
             print("Missing selectedColumns, selectedFrequency, or forecastPeriods in form data")
             return jsonify({"error": "Missing forecasting inputs in request."}), 400

        try:
            selected_columns = json.loads(selected_columns_json)
            date_col = selected_columns.get('Date Column')
            value_col = selected_columns.get('Value Column')
            agg_col = selected_columns.get('Aggregation Column (Optional)')

        except json.JSONDecodeError:
            print("Failed to parse selectedColumns JSON")
            return jsonify({"error": "Invalid format for column selections."}), 400

        selected_freq_code = FREQUENCY_MAP.get(selected_frequency_name)
        if not selected_freq_code:
            print(f"Invalid selected frequency name: {selected_frequency_name}")
            return jsonify({"error": "Invalid forecasting frequency selected."}), 400


        print(f"Received selections (parsed): Date='{date_col}', Value='{value_col}', Aggregation='{agg_col}'")
        print(f"Received frequency: {selected_frequency_name} ({selected_freq_code})")
        print(f"Received forecast periods (string): {forecast_periods_str}")

        if not date_col or not value_col:
             print("Missing required column selections (Date and Value)")
             return jsonify({"error": "Missing required column selections (Date and Value). Please select both."}), 400

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


    # --- Data Processing and Preparation ---
    try:
        file.seek(0)
        df = pd.read_csv(file, keep_default_na=False)

        print(f"Successfully read raw data. DataFrame shape: {df.shape}")
        print(f"Raw DataFrame columns: {df.columns.tolist()}")

        required_cols = [date_col, value_col]
        if agg_col:
             required_cols.append(agg_col)

        for col in required_cols:
            if col not in df.columns:
                print(f"Selected column '{col}' not found in data.")
                return jsonify({"error": f"Selected column '{col}' not found in uploaded data."}), 400

        selected_df = df[required_cols].copy()

        try:
             selected_df[date_col] = pd.to_datetime(selected_df[date_col])
        except Exception as e:
             print(f"Error converting date column '{date_col}' to datetime: {e}")
             return jsonify({"error": f"Failed to convert date column '{date_col}' to datetime. Please ensure it's in a recognizable format.", "details": str(e)}), 400

        # Handle initial aggregation by Date and optional Aggregation column
        if agg_col and agg_col in selected_df.columns:
             print(f"Aggregating data by Date and '{agg_col}'...")
             aggregated_df = selected_df.groupby([date_col, agg_col])[value_col].sum().reset_index()
             print(f"Aggregation complete. Aggregated DataFrame shape: {aggregated_df.shape}")

             print("Further aggregating by Date only to get a single time series...")
             ts_data_initial = aggregated_df.groupby(date_col)[value_col].sum().reset_index()
             print(f"Initial date-aggregated data shape: {ts_data_initial.shape}")

        else:
             print("No aggregation column provided or found. Aggregating by Date only.")
             ts_data_initial = selected_df[[date_col, value_col]].copy()
             ts_data_initial = ts_data_initial.groupby(date_col)[value_col].sum().reset_index()
             print(f"Initial date-aggregated data shape: {ts_data_initial.shape}")


        # Rename columns to generic 'Date' and 'Value' for consistency
        ts_data_initial = ts_data_initial.rename(columns={date_col: 'Date', value_col: 'Value'})

        # Sort by Date and set Date as index
        ts_data_initial = ts_data_initial.sort_values('Date')
        ts_data_initial = ts_data_initial.set_index('Date')

        # Convert Value to numeric and drop NaNs
        ts_data_initial['Value'] = pd.to_numeric(ts_data_initial['Value'], errors='coerce')
        ts_data_initial.dropna(inplace=True)

        # --- Resample to Selected Forecast Frequency ---
        print(f"Resampling data to selected frequency: {selected_frequency_name} ({selected_freq_code})...")
        # Use .resample() with the selected frequency code, aggregate by sum
        # .resample() will handle potential missing periods by default (fills with NaN)
        # Ensure index is datetime before resampling
        ts_data_initial.index = pd.to_datetime(ts_data_initial.index)
        ts_data = ts_data_initial['Value'].resample(selected_freq_code).sum().reset_index()

        # Handle NaNs introduced by resampling (e.g., fill with 0)
        ts_data['Value'].fillna(0, inplace=True) # Fill NaN values with 0

        # Set the resampled date column as the index again
        ts_data = ts_data.set_index('Date')
        # Ensure the resampled index has a frequency set by resample
        if ts_data.index.freq is None:
             print("Warning: Resampled index frequency is None. Attempting to set it.")
             try:
                  ts_data.index.freq = pd.infer_freq(ts_data.index)
                  if ts_data.index.freq is None:
                       print("Warning: Could not infer frequency after resampling. Setting to selected code.")
                       ts_data.index.freq = selected_freq_code # Force set freq code
             except Exception as infer_e:
                  print(f"Error inferring frequency after resampling: {infer_e}. Forcing selected code.")
                  ts_data.index.freq = selected_freq_code # Force set freq code


        # Store the final processed time series data *before* split for returning
        historical_ts_data = ts_data.copy() # Copy for returning later

        print(f"Resampling complete. Final time series data shape ({selected_frequency_name}): {ts_data.shape}")
        print(f"Final time series index frequency: {ts_data.index.freq}")


        if ts_data.empty:
             return jsonify({"error": "Processed time series data is empty after cleaning and resampling."}), 400

        min_data_points = 10 # Minimum points needed for most models/evaluation
        if ts_data.shape[0] < min_data_points:
             return jsonify({"error": f"Not enough data points ({ts_data.shape[0]}) after resampling for forecasting. Need at least {min_data_points} historical data points at the selected frequency."}), 400
        if ts_data.shape[0] <= forecast_periods:
             return jsonify({"error": f"Number of historical data points ({ts_data.shape[0]}) after resampling is not enough to forecast {forecast_periods} periods. Need more historical data than forecast periods."}), 400


        # --- Train/Test Split for Evaluation ---
        # Use 80% for training, 20% for testing
        train_size = int(len(ts_data) * 0.8)
        train_data, test_data = ts_data[0:train_size], ts_data[train_size:]
        print(f"Train data shape: {train_data.shape}, Test data shape: {test_data.shape}")

        # Ensure test set is not empty and has enough points for evaluation
        if test_data.shape[0] == 0:
             # If test set is empty, use a minimum size like 1 or 2 points for test if data allows
             if len(ts_data) >= 2: # Need at least 2 points to have a test set of size 1
                 train_size = len(ts_data) - 1 # Use last point for test
                 train_data, test_data = ts_data[0:train_size], ts_data[train_size:]
                 print(f"Adjusted split: Train data shape: {train_data.shape}, Test data shape: {test_data.shape}")
                 if test_data.shape[0] == 0: # Re-check after adjustment
                       print("Dataset still too small to perform train/test split for evaluation.")
                       perform_evaluation = False
                 else:
                       perform_evaluation = True
             else:
                 print("Dataset too small to perform train/test split for evaluation.")
                 perform_evaluation = False # Disable evaluation
        else:
            perform_evaluation = True


        # --- Implement and Evaluate Multiple Models ---
        evaluation_results = {}
        forecast_results_all_models = {}
        best_method = None
        lowest_rmse = np.inf

        # Define models to run (only those that can be fitted/evaluated)
        models_to_run = ['ARIMA', 'ETS', 'SMA'] # Removed WMA for simplicity initially


        for method_name in models_to_run:
            try:
                print(f"\nRunning and evaluating {method_name}...")
                model_forecast_data = None
                test_rmse = None
                model_fit_obj = None # Store fitted model object if needed for full forecast later

                # --- Fit and Predict on Test Set (for evaluation) ---
                if method_name == 'ARIMA':
                    order = (5, 1, 0) # Fixed ARIMA order
                    if len(train_data) <= order[0] + order[1] + order[2]:
                         print(f"Skipping {method_name} evaluation: Not enough train data ({len(train_data)}) for order {order}.")
                         continue # Skip if not enough data

                    try:
                         model = ARIMA(train_data['Value'], order=order)
                         # Suppress specific ARIMA warnings during fit if needed
                         with warnings.catch_warnings():
                              warnings.filterwarnings("ignore")
                              model_fit = model.fit()

                         # Predict on the test set index dates
                         test_predictions = model_fit.predict(start=test_data.index[0], end=test_data.index[-1])

                     # Catch specific errors during ARIMA fit, e.g., LinAlgError, ValueError
                    except (np.linalg.LinAlgError, ValueError) as arima_fit_error:
                         print(f"ARIMA fitting failed on train data: {arima_fit_error}")
                         continue # Skip evaluation and full forecast for this method on fit failure
                    except Exception as arima_other_error:
                         print(f"Unexpected error during ARIMA fitting on train data: {arima_other_error}")
                         continue # Skip on other errors too


                elif method_name == 'ETS':
                    # Simple Exponential Smoothing
                    if len(train_data) < 2:
                         print(f"Skipping {method_name} evaluation: Not enough train data ({len(train_data)}).")
                         continue

                    try:
                         model = SimpleExpSmoothing(train_data['Value'])
                         model_fit = model.fit(optimized=True) # Optimize alpha
                         # Predict on the test set periods using forecast
                         test_predictions = model_fit.forecast(steps=len(test_data))
                         # Align predictions index with test_data index for RMSE calculation
                         if len(test_predictions) == len(test_data):
                              test_predictions.index = test_data.index
                         else:
                              print(f"Warning: ETS test prediction length ({len(test_predictions)}) mismatch with test data length ({len(test_data)}).")
                              test_predictions = None # Invalidate prediction

                    except Exception as ets_error:
                         print(f"ETS fitting failed on train data: {ets_error}")
                         continue # Skip evaluation and full forecast on fit failure


                elif method_name == 'SMA':
                     window_size = 7 # Example window size (e.g., 7 for weekly data)
                     if len(train_data) < window_size:
                          print(f"Skipping {method_name} evaluation: Not enough train data ({len(train_data)}) for window size {window_size}.")
                          continue

                     # Calculate rolling mean on train data
                     rolling_mean = train_data['Value'].rolling(window=window_size).mean()
                     # The prediction for the test set is the last valid rolling mean value, extended flat
                     if not rolling_mean.empty and not np.isnan(rolling_mean.iloc[-1]):
                         forecast_value = rolling_mean.iloc[-1]
                         test_predictions = pd.Series([forecast_value] * len(test_data), index=test_data.index)
                     else:
                         print("Skipping SMA evaluation: Rolling mean is invalid at the end.")
                         continue # Skip if rolling mean is invalid

                # --- Calculate RMSE on Test Set ---
                if perform_evaluation and test_data.shape[0] > 0 and test_predictions is not None and not test_predictions.empty:
                    # Drop any NaNs that might exist in test_predictions
                    test_predictions.dropna(inplace=True)
                    # Align indices before calculating RMSE to ensure comparing same dates
                    aligned_test_data, aligned_test_predictions = test_data['Value'].align(test_predictions, join='inner')
                    if len(aligned_test_data) > 0: # Ensure there's data after alignment
                        test_rmse = rmse(aligned_test_data, aligned_test_predictions)
                        print(f"{method_name} Test RMSE: {test_rmse}")
                        evaluation_results[method_name] = test_rmse

                        # Update best method if current RMSE is lower (and not infinite/NaN)
                        if test_rmse < lowest_rmse and not np.isnan(test_rmse):
                            lowest_rmse = test_rmse
                            best_method = method_name
                    else:
                         print(f"Skipping {method_name} RMSE calculation: No overlapping index for test data and predictions after alignment.")
                         evaluation_results[method_name] = float('inf') # Assign high RMSE if cannot calculate
                else:
                     print(f"Skipping {method_name} evaluation: Not enough test data, predictions are None, or evaluation disabled.")
                     evaluation_results[method_name] = float('inf') # Assign high RMSE if cannot evaluate


                # --- Generate Forecast on Full Data (for final results) ---
                full_forecast_values = None
                full_conf_int = None

                if method_name == 'ARIMA':
                     order = (5, 1, 0) # Fixed ARIMA order
                     if len(ts_data) <= order[0] + order[1] + order[2]:
                          print(f"Skipping full {method_name} forecast: Not enough data ({len(ts_data)}) for order {order}.")
                          # Mark as failed in results
                          forecast_results_all_models[method_name] = {
                             "evaluation_rmse": evaluation_results.get(method_name, "N/A"),
                             "forecast_data": [],
                             "error": "Not enough data for full model fit"
                         }
                          continue # Skip full forecast

                     try:
                         # Re-fit ARIMA on full data
                         full_model = ARIMA(ts_data['Value'], order=order)
                         with warnings.catch_warnings():
                              warnings.filterwarnings("ignore")
                              full_model_fit = full_model.fit()

                         # Generate forecast for forecast_periods steps
                         forecast_steps_result = full_model_fit.get_forecast(steps=forecast_periods)
                         full_forecast_values = forecast_steps_result.predicted_mean
                         full_conf_int = forecast_steps_result.conf_int() # Confidence intervals

                     except (np.linalg.LinAlgError, ValueError) as arima_fit_error:
                          print(f"Full ARIMA fitting failed: {arima_fit_error}")
                          # Mark as failed in results
                          forecast_results_all_models[method_name] = {
                             "evaluation_rmse": evaluation_results.get(method_name, "N/A"),
                             "forecast_data": [],
                             "error": f"Model fit failed: {arima_fit_error}"
                         }
                          continue # Skip full forecast
                     except Exception as arima_other_error:
                          print(f"Unexpected error during full ARIMA fitting: {arima_other_error}")
                          forecast_results_all_models[method_name] = {
                             "evaluation_rmse": evaluation_results.get(method_name, "N/A"),
                             "forecast_data": [],
                             "error": f"Model fit failed: {arima_other_error}"
                         }
                          continue # Skip full forecast


                elif method_name == 'ETS':
                     if len(ts_data) < 2:
                          print(f"Skipping full {method_name} forecast: Not enough data ({len(ts_data)}).")
                          forecast_results_all_models[method_name] = {
                             "evaluation_rmse": evaluation_results.get(method_name, "N/A"),
                             "forecast_data": [],
                             "error": "Not enough data for full model fit"
                         }
                          continue # Skip full forecast

                     try:
                         # Re-fit ETS on full data
                         full_model = SimpleExpSmoothing(ts_data['Value'])
                         full_model_fit = full_model.fit(optimized=True)
                         # Use forecast() for out-of-sample predictions
                         full_forecast_values = full_model_fit.forecast(steps=forecast_periods)
                         # Simple ETS doesn't provide standard CI in forecast result.
                         # Set placeholder CI for consistency with ARIMA output structure.
                         full_conf_int = pd.DataFrame({
                             0: full_forecast_values, # Lower Bound (placeholder)
                             1: full_forecast_values  # Upper Bound (placeholder)
                         }, index=full_forecast_values.index)

                     except Exception as ets_error:
                         print(f"Full ETS fitting failed: {ets_error}")
                         forecast_results_all_models[method_name] = {
                             "evaluation_rmse": evaluation_results.get(method_name, "N/A"),
                             "forecast_data": [],
                             "error": f"Model fit failed: {ets_error}"
                         }
                         continue # Skip full forecast


                elif method_name == 'SMA':
                     window_size = 7 # Example window size (adjust as needed)
                     if len(ts_data) < window_size:
                          print(f"Skipping full {method_name} forecast: Not enough data ({len(ts_data)}) for window size {window_size}.")
                          forecast_results_all_models[method_name] = {
                             "evaluation_rmse": evaluation_results.get(method_name, "N/A"),
                             "forecast_data": [],
                             "error": f"Not enough data for SMA window size {window_size}"
                         }
                          continue # Skip full forecast

                     # Calculate rolling mean on full data
                     full_rolling_mean = ts_data['Value'].rolling(window=window_size).mean()
                     # The forecast is the last valid rolling mean value, extended flat
                     if not full_rolling_mean.empty and not np.isnan(full_rolling_mean.iloc[-1]):
                         forecast_value = full_rolling_mean.iloc[-1]
                         full_forecast_values = pd.Series([forecast_value] * forecast_periods)
                          # SMA doesn't provide standard CI. Set placeholder CI.
                         full_conf_int = pd.DataFrame({
                             0: full_forecast_values, # Lower Bound (placeholder)
                             1: full_forecast_values  # Upper Bound (placeholder)
                         }, index=full_forecast_values.index)
                     else:
                         print(f"Skipping full {method_name} forecast: Rolling mean is invalid at the end.")
                         forecast_results_all_models[method_name] = {
                             "evaluation_rmse": evaluation_results.get(method_name, "N/A"),
                             "forecast_data": [],
                             "error": "Could not calculate rolling mean for forecast"
                         }
                         continue # Skip full forecast


                # --- Generate Forecast Date Index for Full Forecast ---
                # Need to ensure this index matches the full_forecast_values index length
                last_date = ts_data.index[-1]
                # Use the frequency of the resampled data's index
                used_freq = ts_data.index.freq # Use the frequency from the resampled index (set by resample)

                if used_freq is None:
                     # This should ideally not happen if resample successfully set freq, but keep fallback
                     print("Warning: Resampled index frequency is None after all. Falling back to Daily for forecast index generation.")
                     used_freq = 'D' # Default fallback

                try:
                     # Generate dates starting *after* the last training date, using the determined frequency
                     # Need +1 period to get the date *after* the last historical date
                     # Use the *known* frequency from the resampled index
                     forecast_index_full = pd.date_range(start=last_date, periods=forecast_periods + 1, freq=used_freq)[1:] # Exclude last training date

                except Exception as freq_gen_e:
                     print(f"Could not generate forecast date index with frequency '{used_freq}' for {method_name}. Error: {freq_gen_e}")
                     # Fallback to a simple date range generation if freq generation fails
                     print(f"Falling back to simple daily offset date generation for {method_name}...")
                     forecast_index_full = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=forecast_periods) # Simple daily offset fallback


                # Ensure forecast values length matches forecast date index length
                if full_forecast_values is None or len(forecast_index_full) != len(full_forecast_values):
                     print(f"Warning: Mismatch between forecast index length ({len(forecast_index_full)}) and values length ({len(full_forecast_values) if full_forecast_values is not None else 'None'}) for {method_name}. Skipping forecast data formatting.")
                      # Mark as failed in results
                     forecast_results_all_models[method_name] = {
                         "evaluation_rmse": evaluation_results.get(method_name, "N/A"),
                         "forecast_data": [], # Return empty list
                         "error": "Forecast length mismatch or generation failed"
                     }
                     continue # Skip data formatting if lengths don't match


                # Combine forecast results for this method into a list of dictionaries
                method_forecast_data = []
                for i in range(len(full_forecast_values)): # Iterate based on values length
                     method_forecast_data.append({
                         "Date": forecast_index_full[i].strftime('%Y-%m-%d'),
                         "ForecastValue": float(full_forecast_values.iloc[i]),
                         "LowerBound": float(full_conf_int.iloc[i, 0]) if full_conf_int is not None and full_conf_int.shape[1] > 0 else float(full_forecast_values.iloc[i]), # Handle models without CI easily
                         "UpperBound": float(full_conf_int.iloc[i, 1]) if full_conf_int is not None and full_conf_int.shape[1] > 1 else float(full_forecast_values.iloc[i]) # Handle models without CI easily
                     })

                # Store successful forecast data and evaluation for this model
                forecast_results_all_models[method_name] = {
                     "evaluation_rmse": evaluation_results.get(method_name, "N/A"), # Include test RMSE
                     "forecast_data": method_forecast_data # The forecast points for this method
                }
                print(f"{method_name} forecast generated and formatted.")

            except Exception as e:
                print(f"Error running or evaluating {method_name} (caught late): {e}")
                # Ensure model result is marked as failed if error occurred anywhere in its block
                 if method_name not in forecast_results_all_models or "error" not in forecast_results_all_models[method_name]:
                      forecast_results_all_models[method_name] = {
                         "evaluation_rmse": evaluation_results.get(method_name, float('inf')),
                         "forecast_data": [],
                         "error": f"Runtime error during forecast generation: {str(e)}"
                     }
                 evaluation_results[method_name] = float('inf') # Ensure it's not considered 'best'


        # Determine the best method based on lowest evaluation RMSE among successful evaluations
        best_method = "N/A" # Default if no valid evaluation
        valid_eval_results = {k: v for k, v in evaluation_results.items() if v != float('inf') and not np.isnan(v)}
        if valid_eval_results:
             best_method = min(valid_eval_results, key=valid_eval_results.get)
             print(f"Best method determined based on evaluation: {best_method} (RMSE: {evaluation_results[best_method]})")
        else:
             print("Could not determine best method as all evaluations failed or were skipped.")


        # --- Return Final Results ---
        print("All models attempted. Formatting final response.")
        return jsonify({
            "message": "Forecasts generated successfully",
            "filename": file.filename,
            "selectedColumns": selected_columns,
            "selectedFrequency": selected_frequency_name,
            "forecastPeriods": forecast_periods,
            "bestMethod": best_method, # <--- Indicate the best method name
            "modelResults": forecast_results_all_models, # <--- Include results for all models
            "historicalData": historical_ts_data.reset_index().to_dict(orient='records') # <--- INCLUDE HISTORICAL DATA
        }), 200


    except Exception as e:
        # Catch errors during data reading, processing, or validation before model loop
        print(f"Fatal Error during data processing or model loop setup in /forecast: {e}")
        return jsonify({"error": f"Failed to process uploaded data or setup forecasting models. Details: {str(e)}"}), 500


# --- Frontend Serving Routes ---
def index():
    """Basic route to confirm backend is running."""
    print("--- HITTING BASIC INDEX ROUTE (Frontend Not Served) ---")
    return "Time Series Forecaster Backend is Running! Navigate to the frontend URL."


@app.route('/')
def serve_root_index():
    """Serve index.html for the root path."""
    print("--- ENTERING SERVE ROOT INDEX FUNCTION ---")

    index_html_path = os.path.join(app.static_folder, 'index.html')
    print(f"Root path requested. Trying to serve index.html from: {index_html_path}")

    if os.path.exists(index_html_path):
         print("index.html found at expected static path for root!")
         return send_from_directory(app.static_folder, 'index.html')
    else:
         print("index.html NOT found at the expected static folder path for root.")
         return "Frontend not built or configured correctly (index.html missing at root)", 404


@app.route('/<path:path>')
def serve_static_files(path):
    """
    Serve static files from the frontend build directory for non-root paths.
    """
    print("--- ENTERING SERVE STATIC FILES FUNCTION (Non-Root) ---")
    print(f"Attempting to serve path: /{path}")

    requested_file = os.path.join(app.static_folder, path)
    print(f"Constructed requested file path: {requested_file}")

    try:
        static_folder_abs = os.path.abspath(app.static_folder)
        requested_file_abs = os.path.abspath(requested_file)
        if not requested_file_abs.startswith(static_folder_abs):
             print(f"Security check failed: {requested_file_abs} is not in {static_folder_abs}")
             return "Forbidden", 403
    except Exception as e:
        print(f"Error during path normalization/check: {e}")
        return "Internal Server Error during path check", 500


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


if __name__ == '__main__':
    print("Running Flask app locally (development mode)")
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
