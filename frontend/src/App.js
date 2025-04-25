// frontend/src/App.js
import React, { useState } from 'react'; // Import useState hook
import FileUpload from './components/FileUpload'; // Import the FileUpload component
import './styles/index.css'; // Import your Tailwind CSS file

// This is the main functional component for your application
function App() {
  // State variable to keep track of information after a file is uploaded
  // We initialize it to null, meaning no file has been successfully uploaded yet
  const [uploadInfo, setUploadInfo] = useState(null);

  // This function will be called by the FileUpload component
  // when a file is successfully uploaded to the backend
  const handleFileUploadSuccess = (data) => {
      console.log("File upload successful, received data:", data);
      // Update the state with the data received from the backend
      setUploadInfo(data);
      // TODO: In the next steps, we'll use this uploadInfo to
      // display column selection and forecasting settings
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

        {/* Step 1: File Upload Section */}
        {/* Conditional Rendering: Show FileUpload component only if no file has been successfully uploaded yet */}
        {/* If uploadInfo is null (falsey), render FileUpload */}
        {!uploadInfo && (
            <FileUpload onFileUploadSuccess={handleFileUploadSuccess} />
        )}

        {/* Step 2: Upload Success Message and Placeholder for Next Steps */}
        {/* Conditional Rendering: Show this block only if uploadInfo has data (meaning upload was successful) */}
        {/* If uploadInfo has a value (truthy), render this block */}
        {uploadInfo && (
          <div className="mt-8 p-6 bg-white rounded-lg shadow-md">
            {/* Heading for the success message */}
            <h2 className="text-2xl font-semibold mb-4 text-gray-700">
              File Uploaded Successfully!
            </h2>
            {/* Display the filename received from the backend */}
            <p className="text-gray-600">
              Filename: <span className="font-semibold">{uploadInfo.filename}</span>
            </p>
            {/* Instruction for the next step */}
            <p className="mt-4 text-gray-600">
              Next: Select the date, value, and aggregation columns from your data.
            </p>
            {/* TODO: This is where the Column Selection component will go later */}
          </div>
        )}

        {/* Step 3: Display Results (Will be added later) */}
        {/* TODO: Add component to display chart and table */}

      </div> {/* End of container */}
    </div> // End of main background div
  );
}

export default App; // Export the component so it can be used in index.js
