// frontend/src/App.js
import React, { useState } from 'react';
import FileUpload from './components/FileUpload'; // We will create this component
import './styles/index.css'; // Import Tailwind CSS

function App() {
  const [uploadInfo, setUploadInfo] = useState(null); // To store info after file upload

  const handleFileUploadSuccess = (data) => {
      setUploadInfo(data);
      console.log("File upload successful, received data:", data);
      // TODO: In the next steps, we'll pass this info to the column selection component
  };

  return (
    <div className="min-h-screen bg-gray-100 py-10">
      <div className="container mx-auto px-4 max-w-3xl"> {/* Added max-width for better layout */}
        <h1 className="text-4xl font-bold text-center text-gray-800 mb-10">
          AI Time Series Forecaster
        </h1>

        {/* Step 1: File Upload */}
        {!uploadInfo && (
            <FileUpload onFileUploadSuccess={handleFileUploadSuccess} />
        )}

        {/* Step 2: Column Selection & Settings (Will be added here later) */}
        {uploadInfo && (
          <div className="mt-8 p-6 bg-white rounded-lg shadow-md">
            <h2 className="text-2xl font-semibold mb-4 text-gray-700">File Uploaded Successfully!</h2>
            <p className="text-gray-600">Filename: <span className="font-semibold">{uploadInfo.filename}</span></p>
            <p className="mt-4 text-gray-600">Next: Select the date, value, and aggregation columns from your data.</p>
            {/* Placeholder for Column Selection component */}
          </div>
        )}

        {/* Step 3: Display Results (Will be added later) */}
        {/* TODO: Add component to display chart and table */}

      </div>
    </div>
  );
}

export default App;
