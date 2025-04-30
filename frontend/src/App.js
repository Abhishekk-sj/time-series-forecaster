// frontend/src/App.js
import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import ColumnSelector from './components/ColumnSelector';
import ForecastResults from './components/ForecastResults';
import './styles/index.css';

function App() {
  // State for file upload info from backend (/upload response)
  const [uploadInfo, setUploadInfo] = useState(null);
  // State for storing the original file object received in handleFileUploadSuccess
  const [uploadedFile, setUploadedFile] = useState(null);

  // *** Removed: selectedColumns state is no longer needed in App.js for rendering flow ***
  // const [selectedColumns, setSelectedColumns] = useState(null); // eslint-disable-next-line no-unused-vars

  // State for forecasting results received from backend (/forecast response)
  const [forecastResults, setForecastResults] = useState(null);


  // Function called by FileUpload on success
  const handleFileUploadSuccess = (data, file) => {
      console.log("File upload successful, received data:", data);
      console.log("Original file object received:", file);
      setUploadInfo(data); // Store backend response (headers, etc.)
      setUploadedFile(file); // STORE THE ORIGINAL FILE OBJECT

      // Reset states for the next steps
      // *** Removed: setSelectedColumns(null) ***
      setForecastResults(null); // Reset forecast results
  };

  // *** Removed: handleColumnsSelected function is no longer needed in App.js ***
  // const handleColumnsSelected = (selections) => { // eslint-disable-next-line no-unused-vars
  //     console.log("Columns selected:", selections);
  //     // setSelectedColumns(selections); // No longer setting this state here
  // };

   // Function called by ColumnSelector when the backend returns forecast results
   const handleForecastComplete = (results) => {
       console.log("Forecasting completed, received results:", results);
       setForecastResults(results); // Store the results received from the backend's /forecast endpoint
       // We might clear previous states here to allow re-uploading if needed
       // setUploadInfo(null);
       // setUploadedFile(null);
   };


  return (
    <div className="min-h-screen bg-gray-100 py-10">
      <div className="container mx-auto px-4 max-w-3xl">

        <h1 className="text-4xl font-bold text-center text-gray-800 mb-10">
          AI Time Series Forecaster
        </h1>

        {/* Conditional Rendering */}

        {/* Step 1: File Upload */}
        {/* Show FileUpload component if no upload info AND no file object stored yet AND no forecast results */}
        {!uploadInfo && !uploadedFile && !forecastResults && ( // Added !forecastResults check
            <FileUpload onFileUploadSuccess={handleFileUploadSuccess} />
        )}

        {/* Step 2: Column Selection and Run Forecast */}
        {/* Show ColumnSelector if upload info AND file object are available, AND forecast results are NOT available */}
        {uploadInfo && uploadedFile && !forecastResults && (
             <ColumnSelector
                columnHeaders={uploadInfo.column_headers}
                file={uploadedFile}
                onForecastComplete={handleForecastComplete}
                // onColumnsSelected={handleColumnsSelected} // No longer passed
             />
        )}

        {/* Step 3: Display Forecasting Results */}
        {/* Show ForecastResults component if forecast results ARE available */}
        {forecastResults && (
             <ForecastResults results={forecastResults} />
        )}

         {/* Optional: Button to restart the process */}
         {/* Show a restart button if forecast results are present */}
         {forecastResults && (
              <div className="mt-8 flex justify-center">
                   <button
                        onClick={() => { // Inline function to reset states
                            setUploadInfo(null);
                            setUploadedFile(null);
                            setForecastResults(null);
                            // *** Removed: setSelectedColumns(null); ***
                        }}
                        className="px-6 py-2 bg-gray-300 text-gray-700 font-semibold rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-opacity-50"
                   >
                        Upload Another File
                   </button>
              </div>
         )}


      </div>
    </div>
  );
}

export default App;
