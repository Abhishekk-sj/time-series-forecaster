// frontend/src/components/FileUpload.js
import React, { useState } from 'react';
import axios from 'axios'; // For making HTTP requests

// IMPORTANT: Replace with your actual Render backend URL
// Example: https://your-backend-service.onrender.com
const BACKEND_URL = 'https://time-series-forecaster-backend.onrender.com'; // <-- *** REPLACE THIS ***

function FileUpload({ onFileUploadSuccess }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file && file.name.endsWith('.csv')) {
        setSelectedFile(file);
        setMessage(''); // Clear previous messages
    } else {
        setSelectedFile(null);
        setMessage('Please select a valid CSV file.');
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage('Please select a file first!');
      return;
    }

    // Basic check for the placeholder URL
    if (BACKEND_URL === 'https://time-series-forecaster-backend.onrender.com') {
         setMessage('Error: Backend URL is not configured. Please update FileUpload.js.');
         console.error('Backend URL is not configured in FileUpload.js');
         return;
    }


    const formData = new FormData();
    formData.append('file', selectedFile);

    setIsLoading(true);
    setMessage('Uploading...');

    try {
      // POST request to your deployed Render backend /upload endpoint
      const response = await axios.post(`${BACKEND_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data', // axios sets this correctly for FormData
        },
        // Add a timeout in case the backend is slow or unresponsive
        timeout: 30000 // 30 seconds
      });

      // Assuming the backend responds with JSON like:
      // {"message": "File uploaded successfully", "filename": "...", ...}
      setMessage('Upload successful!');
      console.log('Upload response:', response.data);
      if (onFileUploadSuccess) {
          // Pass the backend response data up to the parent (App.js)
          onFileUploadSuccess(response.data);
      }
    } catch (error) {
      console.error('Upload failed:', error);
      let errorMessage = 'Upload failed.';
      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        errorMessage = `Upload failed: ${error.response.status} - ${error.response.data?.error || error.statusText}`;
      } else if (error.request) {
        // The request was made but no response was received
        errorMessage = 'Upload failed: No response from server. Is the backend running?';
      } else {
        // Something happened in setting up the request that triggered an Error
        errorMessage = `Upload failed: ${error.message}`;
      }
       setMessage(errorMessage);

    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="mt-8 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-semibold mb-4 text-gray-700">Step 1: Upload Time Series Data</h2>
       {/* Instruction */}
      <p className="mb-4 text-gray-600 text-sm">
          Please upload a CSV file containing your time series data. Ensure it has at least a date column and a value column.
      </p>
      <div className="flex flex-col sm:flex-row items-center space-y-4 sm:space-y-0 sm:space-x-4"> {/* Responsive layout */}
        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          className="block w-full text-sm text-gray-500
            file:mr-4 file:py-2 file:px-4
            file:rounded-full file:border-0
            file:text-sm file:font-semibold
            file:bg-blue-50 file:text-blue-700
            hover:file:bg-blue-100 cursor-pointer"
        />
        <button
          onClick={handleUpload}
          disabled={!selectedFile || isLoading || BACKEND_URL === 'https://time-series-forecaster-backend.onrender.com'}
          className={`px-6 py-2 text-white font-semibold rounded-md flex-shrink-0
            ${selectedFile && !isLoading && BACKEND_URL !== 'https://time-series-forecaster-backend.onrender.com' ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-400 cursor-not-allowed'}
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50`}
        >
          {isLoading ? 'Uploading...' : 'Upload File'}
        </button>
      </div>
      {message && (
        <p className={`mt-4 text-sm ${message.includes('successful') ? 'text-green-600' : 'text-red-500'}`}>
          {message}
        </p>
      )}
      {selectedFile && !isLoading && !message && ( // Show selected file name before upload attempt
           <p className="mt-2 text-sm text-gray-700">Selected: <span className="font-semibold">{selectedFile.name}</span></p>
      )}
       {selectedFile && !isLoading && message.includes('successful') && (
          <p className="mt-2 text-sm text-gray-700">Uploaded: <span className="font-semibold">{selectedFile.name}</span></p>
      )}
    </div>
  );
}

export default FileUpload;
