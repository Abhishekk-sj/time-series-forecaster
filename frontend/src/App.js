// frontend/src/App.js
import React, { useState } from 'react'; // Import useState hook
import FileUpload from './components/FileUpload'; // Import the FileUpload component
import ColumnSelector from './components/ColumnSelector'; // Import the ColumnSelector component
import './styles/index.css'; // Import your Tailwind CSS file

// This is the main functional component for your application
function App() {
  // State variable to keep track of information after a file is uploaded
  // Will store the response from the backend's /upload endpoint (includes filename, column_headers)
  const [uploadInfo, setUploadInfo] = useState(null);

  // State variable to store the user's selected columns for forecasting
  // Will store the selections made in the ColumnSelector component
  const [selectedColumns, setSelectedColumns] = useState(null);

  // *** Removed: forecastResults state variable declaration temporary ***
  // const [forecastResults, setForecastResults] = useState(null); // Will be added back later


  // Function called by the FileUpload component when a file is successfully uploaded
  const handleFileUploadSuccess = (data) => {
      console.log("File upload successful, received data:", data);
      // Update the state with the data received from the backend (/upload response)
      setUploadInfo(data);
      // Reset selected columns when a new file is uploaded
      setSelectedColumns(null);
      // *** Removed: setForecastResults(null) temporary ***
      // setForecastResults(null); // Reset forecast results too
  };

  // Function called by the ColumnSelector component when the user confirms selections
  const handleColumnsSelected = (selections) => {
      console.log("Columns selected:", selections);
      // Store the user's selected columns in state
      setSelectedColumns(selections);
      // TODO: In the next step, we will use selections and uploadInfo
      // to call the backend's forecasting API
  };


  // --- TODO: Add handleForecastResults function here later ---
  // This function will be called after the backend returns forecasting results.
  // It will receive the results data as an argument.
  // const handleForecastResults = (results) => {
  //    console.log("Forecasting completed, received results:", results);
  //    // Need forecastResults state here later
  //    // setForecastResults(results);
  // };


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

        {/* Case 1: File Upload is needed */}
        {/* Show FileUpload component only if no file has been successfully uploaded yet (uploadInfo is null) */}
        {!uploadInfo && (
            <FileUpload onFileUploadSuccess={handleFileUploadSuccess} />
        )}

        {/* Case 2: Columns need to be selected */}
        {/* Show ColumnSelector if uploadInfo is available (file uploaded) AND columns have NOT been selected yet (selectedColumns is null) */}
        {uploadInfo && !selectedColumns && (
            // Render the ColumnSelector component
            // Pass the columnHeaders from the uploadInfo received from backend
            // Pass the handleColumnsSelected function as a callback
            <ColumnSelector
                columnHeaders={uploadInfo.column_headers} // <--- Pass headers here
                onColumnsSelected={handleColumnsSelected} // <--- Pass callback here
            />
        )}

        {/* Case 3: Display Forecasting Results */}
        {/* Show Results component if columns HAVE been selected AND forecast results ARE available */}
        {/* *** Removed: Conditional rendering based on forecastResults temporary *** */}
        {/* {selectedColumns && forecastResults && (
            <ForecastResults results={forecastResults} />
        )} */}

         {/* Optional: Placeholder if columns selected but results not yet available (e.g., loading) */}
         {/* *** Removed: Conditional rendering based on !forecastResults temporary *** */}
         {/* {selectedColumns && !forecastResults && (
              <div className="mt-8 p-6 bg-white rounded-lg shadow-md">
                   <h2 className="text-2xl font-semibold mb-4 text-gray-700">
                     Processing Forecast...
                   </h2>
                   <p className="text-gray-600">Please wait while the forecast is being generated.</p>
              </div>
         )} */}


      </div> {/* End of container */}
    </div> // End of main background div
  );
}

export default App; // Export the component
