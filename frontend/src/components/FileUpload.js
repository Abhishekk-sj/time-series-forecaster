// frontend/src/components/FileUpload.js
import React, { useState } from 'react';
import axios from 'axios';

// Your actual Render backend URL provided by you
const BACKEND_URL = 'https://time-series-forecaster-backend.onrender.com';

// This component handles selecting and uploading a file
function FileUpload({ onFileUploadSuccess }) {
  // State to hold the selected file object
  const [selectedFile, setSelectedFile] = useState(null);
  // State for displaying messages to the user (upload status, errors)
  const [message, setMessage] = useState('');
  // State to indicate if upload is in progress (for button disabling/loading)
  const [isLoading, setIsLoading] = useState(false);


  // Function called when the user selects a file via the input
  const handleFileSelect = (event) => {
    // Get the selected file object from the input event
    const file = event.target.files[0];
    // Check if a file was actually selected
    if (file) {
      // Check if the selected file is a CSV
      if (file.name.endsWith('.csv')) {
        setSelectedFile(file); // Store the file object in state
        setMessage(`File selected: ${file.name}`); // Update message
        // Clear any previous error messages
        if (message.startsWith('Error:')) {
            setMessage('');
        }
      } else {
        // If not a CSV, clear the selected file and show an error
        setSelectedFile(null);
        setMessage('Error: Please select a CSV file.');
      }
    } else {
        // If no file was selected (e.g., user cancelled file picker)
        setSelectedFile(null);
        setMessage(''); // Clear message if no file is selected
    }
  };

  // Function called when the user clicks the upload button
  const handleFileUpload = async () => {
    // Check if a file is selected before attempting upload
    if (!selectedFile) {
      setMessage('Please select a file first.');
      return; // Stop the function if no file is selected
    }

    setMessage('Uploading...'); // Update message to indicate upload is starting
    setIsLoading(true); // Set loading state to true

    // Create a FormData object to send the file
    const formData = new FormData();
    // Append the selected file under the key 'file' (must match backend expectation)
    formData.append('file', selectedFile);

    console.log(`Attempting to upload to: ${BACKEND_URL}/upload`); // Debug log

    try {
      // Use axios to send a POST request to the backend's /upload endpoint
      const response = await axios.post(`${BACKEND_URL}/upload`, formData, {
         // axios sets Content-Type: multipart/form-data automatically with FormData
         timeout: 30000 // 30 seconds timeout (adjust as needed)
      });

      // If the request is successful (status 2xx)
      console.log('Upload response:', response.data); // Log the response from the backend

      // Call the parent component's callback function, passing the data
      if (onFileUploadSuccess) {
          // >>>>>>> CHANGE THIS LINE <<<<<<<
          // Pass BOTH the response data AND the original selectedFile object
          onFileUploadSuccess(response.data, selectedFile); // <--- Pass response.data AND selectedFile
          // >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
      }

      //setMessage('File uploaded successfully!'); // Message is now handled by App.js rendering next step

    } catch (error) {
      // If there's an error during the request
      console.error('Upload failed:', error); // Log the error
      setIsLoading(false); // Set loading state back to false
      let displayError = 'Upload failed.';

      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        console.error('Error response data:', error.response.data);
        console.error('Error response status:', error.response.status);
        console.error('Error response headers:', error.response.headers);
        displayError = `Upload failed: ${error.response.status} - ${error.response.data?.error || error.response.statusText || 'Unknown Error'}`;
      } else if (error.request) {
        // The request was made but no response was received
        // `error.request` is an instance of XMLHttpRequest in the browser and an instance of
        // http.ClientRequest in node.js
        displayError = 'Upload failed: No response from server. Is the backend running?';
      } else {
        // Something happened in setting up the request that triggered an Error
        displayError = `Upload failed: ${error.message}`;
      }
       setMessage(`Error: ${displayError}`); // Display the error message to the user

    } finally {
      // This block will always execute after try/catch
      setIsLoading(false); // Ensure loading state is false whether success or failure
    }
  };


  return (
    // Container div for the file upload form with Tailwind styling
    <div className="mt-8 p-6 bg-white rounded-lg shadow-md">
      {/* Section Title */}
      <h2 className="text-2xl font-semibold mb-4 text-gray-700">
        Step 1: Upload CSV Data
      </h2>

      {/* Instruction for the user */}
      <p className="mb-4 text-gray-600 text-sm">
        Upload a CSV file containing your time series data. Ensure it has a date column and a value column.
      </p>

      {/* File Input Element */}
      <div className="mb-4">
        <label htmlFor="file-upload" className="block text-sm font-medium text-gray-700 mb-2">
          Select file:
        </label>
        <input
          type="file" // Specifies this is a file input
          id="file-upload" // Connects to the label
          accept=".csv" // Restricts file picker to CSV files
          onChange={handleFileSelect} // Calls our handler when a file is selected
          // Tailwind classes for styling - may vary based on browser
          className="block w-full text-sm text-gray-500
            file:mr-4 file:py-2 file:px-4
            file:rounded-md file:border-0
            file:text-sm file:font-semibold
            file:bg-blue-50 file:text-blue-700
            hover:file:bg-blue-100"
        />
      </div>

      {/* Display messages to the user */}
      {message && (
        // Conditional styling based on whether the message is an error or success/info
        <p className={`mt-2 text-sm ${message.startsWith('Error:') ? 'text-red-500' : 'text-gray-600'}`}>
          {message}
        </p>
      )}

      {/* Upload Button */}
      <div className="mt-6 flex justify-end">
        <button
          onClick={handleFileUpload} // Calls our handler when clicked
          disabled={!selectedFile || isLoading} // Button disabled if no file selected or if loading
          // Tailwind classes for button styling, conditional styling based on disabled state
          className={`px-6 py-2 text-white font-semibold rounded-md
            ${selectedFile && !isLoading ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-400 cursor-not-allowed'}
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 flex items-center`} // Added flex and items-center for loading spinner
        >
          {/* Show loading spinner if loading */}
           {isLoading && (
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            )}
          {/* Button text changes based on loading state */}
          {isLoading ? 'Uploading...' : 'Upload File'}
        </button>
      </div>

    </div> // End of main container div
  );
}

export default FileUpload; // Export the component for use in App.js
