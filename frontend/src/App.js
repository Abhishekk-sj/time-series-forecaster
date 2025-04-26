// frontend/src/App.js
import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import ColumnSelector from './components/ColumnSelector';
// TODO: Import ForecastResults component later
// import ForecastResults from './components/ForecastResults';
import './styles/index.css';

function App() {
  // State for file upload info from backend (/upload response)
  const [uploadInfo, setUploadInfo] = useState(null);
  // State for storing the original file object received in handleFileUploadSuccess
  const [uploadedFile, setUploadedFile] = useState(null); // <--- NEW STATE FOR FILE

  // State for user's selected columns from ColumnSelector
  const [selectedColumns, setSelectedColumns] = useState(null); // This is set after column selections are confirmed

  // State for forecasting results received from backend (/forecast response)
  const [forecastResults, setForecastResults] = useState(null); // <--- ADDED BACK forecastResults state


  // Function called by FileUpload on success
  const handleFileUploadSuccess = (data, file) => { // <--- NOW RECEIVES FILE OBJECT
      console.log("File upload successful, received data:", data);
      console.log("Original file object received:", file);
      setUploadInfo(data); // Store backend response (headers, etc.)
      setUploadedFile(file); // <--- STORE THE ORIGINAL FILE OBJECT

      // Reset states for the next steps
      setSelectedColumns(null);
      setForecastResults(null);
  };

  // Function called by ColumnSelector when user confirms selections (before calling forecast API)
  const handleColumnsSelected = (selections) => {
      console.log("Columns selected:", selections);
      // Store the selections made by the user.
      // The forecasting API call logic has been moved to ColumnSelector.js
      // We set this state here just to potentially control rendering between steps if needed.
      setSelectedColumns(selections);
       // We don't set forecastResults here, it's set after the /forecast API call
  };

   // Function called by ColumnSelector when the backend returns forecast results
   const handleForecastComplete = (results) => { // <--- NEW HANDLER FOR FORECAST RESULTS
       console.log("Forecasting completed, received results:", results);
       // Store the results received from the backend's /forecast endpoint
       setForecastResults(results);
       // We might clear selectedColumns or uploadInfo here depending on desired flow
   };


  return (
    <div className="min-h-screen bg-gray-100 py-10">
      <div className="container mx-auto px-4 max-w-3xl">

        <h1 className="text-4xl font-bold text-center text-gray-800 mb-10">
          AI Time Series Forecaster
        </h1>

        {/* Conditional Rendering */}

        {/* Step 1: File Upload */}
        {/* Show FileUpload if no upload info AND no file object stored yet */}
        {!uploadInfo && !uploadedFile && (
            <FileUpload onFileUploadSuccess={handleFileUploadSuccess} />
        )}

        {/* Step 2: Column Selection and Run Forecast */}
        {/* Show ColumnSelector if upload info AND file object are available, AND forecast results are NOT available */}
        {uploadInfo && uploadedFile && !forecastResults && ( // <--- Added uploadedFile check and !forecastResults
             // Render ColumnSelector
             // Pass headers, the original file object, and the forecast complete handler
            <ColumnSelector
                columnHeaders={uploadInfo.column_headers}
                file={uploadedFile} // <--- PASS THE FILE OBJECT
                onForecastComplete={handleForecastComplete} // <--- PASS THE NEW HANDLER
                // We no longer pass onColumnsSelected for state update here,
                // as the forecast call is triggered directly in ColumnSelector.
                // If you need the selections state in App.js, you can keep setting it in a simplified onColumnsSelected.
                // For now, let's simplify the flow slightly.
            />
        )}

        {/* Step 3: Display Forecasting Results */}
        {/* Show Results component if forecast results ARE available */}
        {/* TODO: Build and import ForecastResults component */}
        {forecastResults && ( // <--- Show if forecastResults is set
             <div className="mt-8 p-6 bg-white rounded-lg shadow-md">
                 <h2 className="text-2xl font-semibold mb-4 text-gray-700">
                   Forecasting Results
                 </h2>
                 {/* Placeholder for results */}
                 <p>Results received:</p>
                 <pre className="overflow-auto text-sm bg-gray-100 p-4 rounded">{JSON.stringify(forecastResults, null, 2)}</pre>
             </div>
        )}


      </div>
    </div>
  );
}

export default App;
