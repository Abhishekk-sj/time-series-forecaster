// frontend/src/App.js
import React, { useState } from 'react'; // Import useState hook
import FileUpload from './components/FileUpload'; // Import the FileUpload component
import ColumnSelector from './components/ColumnSelector'; // Import the ColumnSelector component
// TODO: Import ForecastResults component later
// import ForecastResults from './components/ForecastResults';
import './styles/index.css'; // Import your Tailwind CSS file

function App() {
  // State variable to keep track of information after a file is uploaded
  // Will store the response from the backend's /upload endpoint (includes filename, column_headers)
  const [uploadInfo, setUploadInfo] = useState(null);

  // State variable to store the user's selected columns for forecasting
  // Will store the selections made in the ColumnSelector component
  // This is used to decide WHEN to show the next step, but its value isn't directly rendered yet.
  const [selectedColumns, setSelectedColumns] = useState(null); // eslint-disable-next-line no-unused-vars

  // State variable for storing the original file object received in handleFileUploadSuccess
  const [uploadedFile, setUploadedFile] = useState(null); // NEW STATE FOR FILE

  // State variable to store the forecasting results received from the backend (/forecast response)
  // This variable is not used yet, but will be in future steps.
  const [forecastResults, setForecastResults] = useState(null); // Will be added back later


  // Function called by FileUpload on success
  // It receives the backend's response data AND the original file object.
  const handleFileUploadSuccess = (data, file) => {
      console.log("File upload successful, received data:", data);
      console.log("Original file object received:", file);
      setUploadInfo(data); // Store backend response (headers, etc.)
      setUploadedFile(file); // STORE THE ORIGINAL FILE OBJECT

      // Reset states for the next steps
      setSelectedColumns(null);
      setForecastResults(null);
  };

  // Function called by ColumnSelector when user confirms selections (before calling forecast API)
  // We added the forecast API call logic directly into ColumnSelector, so this function's
  // primary purpose now is just to update the selectedColumns state in App.js IF needed for rendering logic.
  // As forecast call is in ColumnSelector, this fn isn't strictly needed for the *flow* anymore,
  // but we'll keep setting the state for potential future use or rendering logic.
  // The comment below tells ESLint to ignore the 'no-unused-vars' warning for this function definition.
  const handleColumnsSelected = (selections) => { // eslint-disable-next-line no-unused-vars
      console.log("Columns selected:", selections);
      // Store the user's selected columns in state
      setSelectedColumns(selections);
       // We don't set forecastResults here, it's set after the /forecast API call
  };

   // Function called by ColumnSelector when the backend returns forecast results
   // This function will be called after the backend returns forecasting results.
   // It will receive the results data as an argument.
   const handleForecastComplete = (results) => {
       console.log("Forecasting completed, received results:", results);
       // Store the results received from the backend's /forecast endpoint
       setForecastResults(results);
       // We might clear selectedColumns or uploadInfo here depending on desired flow
   };


  return (
    // Use Tailwind classes for styling - min-h-screen makes it at least full height
    <div className="min-h-screen bg-gray-100 py-10">
      {/* Container to center content and limit its width */}
      <div className="container mx-auto px-4 max-w-3xl">

        {/* Application Title */}
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
                // We are no longer passing onColumnsSelected here for state update in App.js
                // onColumnsSelected={handleColumnsSelected}
            />
        )}

        {/* Step 3: Display Forecasting Results */}
        {/* Show Results component if forecast results ARE available */}
        {/* TODO: Build and import ForecastResults component */}
        {forecastResults && ( // Show if forecastResults is set
             <div className="mt-8 p-6 bg-white rounded-lg shadow-md">
                 <h2 className="text-2xl font-semibold mb-4 text-gray-700">
                   Forecasting Results
                 </h2>
                 {/* Placeholder for results */}
                 <p>Results received:</p>
                 {/* Display the received JSON response */}
                 <pre className="overflow-auto text-sm bg-gray-100 p-4 rounded">{JSON.stringify(forecastResults, null, 2)}</pre>
             </div>
        )}

         {/* Optional: Placeholder if columns selected but results not yet available (e.g., loading) */}
         {/* This placeholder is shown if upload is complete, file is stored, columns selected (handled by ColumnSelector's state/logic), and forecast results are not yet available */}
         {/* Note: The logic to *show* a loading indicator is now primarily within ColumnSelector */}
         {/* {uploadInfo && uploadedFile && !forecastResults && selectedColumns && ( // Refined condition */}
         {/* Removed this block temporarily to simplify until needed */}
         {/* )} */}


      </div>
    </div>
  );
}

export default App; // Export the component
