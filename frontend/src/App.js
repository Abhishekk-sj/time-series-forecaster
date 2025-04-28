// frontend/src/App.js
import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import ColumnSelector from './components/ColumnSelector';
import ForecastResults from './components/ForecastResults'; // <--- IMPORT ForecastResults component
import './styles/index.css';

function App() {
  // State for file upload info from backend (/upload response)
  const [uploadInfo, setUploadInfo] = useState(null);
  // State for storing the original file object received in handleFileUploadSuccess
  const [uploadedFile, setUploadedFile] = useState(null);

  // State for user's selected columns from ColumnSelector (kept for potential future use, but not directly rendered)
  const [selectedColumns, setSelectedColumns] = useState(null); // eslint-disable-next-line no-unused-vars

  // State for forecasting results received from backend (/forecast response)
  const [forecastResults, setForecastResults] = useState(null);


  // Function called by FileUpload on success
  const handleFileUploadSuccess = (data, file) => {
      console.log("File upload successful, received data:", data);
      console.log("Original file object received:", file);
      setUploadInfo(data); // Store backend response (headers, etc.)
      setUploadedFile(file); // STORE THE ORIGINAL FILE OBJECT

      // Reset states for the next steps
      setSelectedColumns(null);
      setForecastResults(null);
  };

  // Function called by ColumnSelector when user confirms selections (API call is now in ColumnSelector)
  // This function is primarily here to update the selectedColumns state in App.js if needed for rendering logic.
  const handleColumnsSelected = (selections) => { // eslint-disable-next-line no-unused-vars
      console.log("Columns selected:", selections);
      setSelectedColumns(selections); // Store the user's selected columns
       // forecastResults is set by handleForecastComplete
  };

   // Function called by ColumnSelector when the backend returns forecast results
   const handleForecastComplete = (results) => {
       console.log("Forecasting completed, received results:", results);
       // Store the results received from the backend's /forecast endpoint
       setForecastResults(results);
       // We might clear selectedColumns or uploadInfo here depending on desired flow (e.g., go back to upload)
       // For now, keep previous info visible alongside results.
   };


  return (
    <div className="min-h-screen bg-gray-100 py-10">
      <div className="container mx-auto px-4 max-w-3xl">

        <h1 className="text-4xl font-bold text-center text-gray-800 mb-10">
          AI Time Series Forecaster
        </h1>

        {/* Conditional Rendering based on application state */}

        {/* Step 1: File Upload */}
        {/* Show FileUpload component only if no upload info AND no file object stored yet */}
        {!uploadInfo && !uploadedFile && (
            <FileUpload onFileUploadSuccess={handleFileUploadSuccess} />
        )}

        {/* Step 2: Column Selection and Run Forecast */}
        {/* Show ColumnSelector if upload info AND file object are available, AND forecast results are NOT available */}
        {uploadInfo && uploadedFile && !forecastResults && (
             // Render ColumnSelector
             // Pass headers, the original file object, and the forecast complete handler
            <ColumnSelector
                columnHeaders={uploadInfo.column_headers}
                file={uploadedFile} // PASS THE FILE OBJECT
                onForecastComplete={handleForecastComplete} // PASS THE NEW HANDLER
                // onColumnsSelected={handleColumnsSelected} // Not directly needed for flow now
            />
        )}

        {/* Step 3: Display Forecasting Results */}
        {/* Show ForecastResults component if forecast results ARE available */}
        {/* >>>>> REPLACE THE PLACEHOLDER JSON DISPLAY WITH ForecastResults COMPONENT <<<<< */}
        {forecastResults && ( // Show if forecastResults is set
             // Render the ForecastResults component, passing the received data
             <ForecastResults results={forecastResults} />
        )}
        {/* >>>>> END OF REPLACEMENT <<<<< */}


         {/* Optional: Placeholder for loading state (handled within ColumnSelector now) */}
         {/* Removed this block temporarily */}


      </div>
    </div>
  );
}

export default App;
