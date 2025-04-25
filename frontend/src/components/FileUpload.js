// frontend/src/components/FileUpload.js
import React, { useState } from 'react';
import axios from 'axios'; // Import axios for making HTTP requests

// Your actual Render backend URL provided by you
const BACKEND_URL = 'https://time-series-forecaster-backend.onrender.com';

// Placeholder value to check if the URL was ever intended to be replaced
const PLACEHOLDER_BACKEND_URL_CHECK = 'YOUR_RENDER_BACKEND_URL_HERE';

function FileUpload({ onFileUploadSuccess }) {
  // State to hold the file the user selects
  const [selectedFile, setSelectedFile] = useState(null);
  // State to hold messages for the user (e.g., "Uploading...", "Upload successful!")
  const [message, setMessage] = useState('');
  // State to indicate if the upload is currently in progress
  const [isLoading, setIsLoading] = useState(false);

  // Function called when the user selects a file
  const handleFileChange = (event) => {
    const file = event.target.files[0]; // Get the first file selected
    // Check if a file was selected and if its name ends with .csv
    if (file && file.name.endsWith('.csv')) {
        setSelectedFile(file); // Store the selected file in state
        setMessage(''); // Clear any previous messages
    } else {
        // If no file or not a CSV, clear selected file and show an error message
        setSelectedFile(null);
        setMessage('Please select a valid CSV file.');
    }
  };

  // Function called when the user clicks the "Upload" button
  const handleUpload = async () => {
    // Prevent upload if no file is selected
    if (!selectedFile) {
      setMessage('Please select a file first!');
      return; // Stop the function here
    }

    // This check now just ensures the *original* placeholder wasn't somehow used
    // Since we hardcoded your URL, this check might be less critical now but kept for robustness
    if (BACKEND_URL === PLACEHOLDER_BACKEND_URL_CHECK) {
         setMessage('Error: Backend URL is still the placeholder.');
         console.error('Backend URL is still the placeholder.');
         return;
    }

    // Create a FormData object to send the file
    const formData = new FormData();
    // Append the selected file to the form data with the key 'file'
    // The backend expects the file under the key 'file' (request.files['file'])
    formData.append('file', selectedFile);

    setIsLoading(true); // Set loading state to true
    setMessage('Uploading...'); // Show an uploading message

    try {
      // Use axios to send a POST request to the backend's /upload endpoint
      // The URL is constructed using the BACKEND_URL constant
      console.log(`Attempting to upload to: ${BACKEND_URL}/upload`); // Debug log in browser console
      const response = await axios.post(`${BACKEND_URL}/upload`, formData, {
        // headers: {'Content-Type': 'multipart/form-data'} // axios sets this automatically for FormData
        timeout: 30000 // Set a timeout for the request (e.g., 30 seconds)
      });

      // If the request is successful (status 2xx)
      setMessage('Upload successful!'); // Show success message
      console.log('Upload response:', response.data); // Log the response from the backend
      // Call the parent component's success handler, passing the backend data
      if (onFileUploadSuccess) {
          onFileUploadSuccess(response.data);
      }

    } catch (error) {
      // If there's an error during the request
      console.error('Upload failed:', error); // Log the error
      let errorMessage = 'Upload failed.'; // Default error message

      // Provide more specific error messages based on the axios error type
      if (error.response) {
        // The server responded with a status code outside of 2xx (e.g., 404, 405, 500)
        errorMessage = `Upload failed: ${error.response.status} - ${error.response.data?.error || error.response.statusText || 'Unknown Error'}`;
      } else if (error.request) {
        // The request was sent but no response was received (e.g., network error, backend down, CORS issue)
        errorMessage = 'Upload failed: No response from server. Is the backend running?';
      } else {
        // Something else went wrong setting up the request
        errorMessage = `Upload failed: ${error.message}`;
      }
       setMessage(errorMessage); // Display the error message to the user

    } finally {
      // This block runs regardless of success or failure
      setIsLoading(false); // Set loading state back to false
    }
  };

  // The JSX that defines the component's UI
  return (
    // Main container div with some Tailwind styling for appearance and spacing
    <div className="mt-8 p-6 bg-white rounded-lg shadow-md">

      {/* Section Title */}
      <h2 className="text-2xl font-semibold mb-4 text-gray-700">
        Step 1: Upload Time Series Data
      </h2>

      {/* Instruction for the user */}
      <p className="mb-4 text-gray-600 text-sm">
          Please upload a CSV file containing your time series data. Ensure it has at least a date column and a value column.
      </p>

      {/* Container for file input and button - uses flexbox for layout */}
      {/* sm:flex-row makes it a row on small screens and up, flex-col by default */}
      <div className="flex flex-col sm:flex-row items-center space-y-4 sm:space-y-0 sm:space-x-4">

        {/* File Input Element */}
        <input
          type="file"        // Specifies this is a file input
          accept=".csv"      // Suggests to the browser to only allow CSV files
          onChange={handleFileChange} // Calls our handleFileChange function when a file is selected
          // Tailwind classes for styling the file input (note the 'file:' prefix)
          className="block w-full text-sm text-gray-500
            file:mr-4 file:py-2 file:px-4
            file:rounded-full file:border-0
            file:text-sm file:font-semibold
            file:bg-blue-50 file:text-blue-700
            hover:file:bg-blue-100 cursor-pointer"
        />

        {/* Upload Button */}
        <button
          onClick={handleUpload} // Calls our handleUpload function when clicked
          // Button is disabled if no file is selected, upload is in progress,
          // or if the backend URL is still the placeholder (shouldn't happen now)
          disabled={!selectedFile || isLoading || BACKEND_URL === PLACEHOLDER_BACKEND_URL_CHECK}
          // Tailwind classes for button styling, including conditional styling based on disabled state
          className={`px-6 py-2 text-white font-semibold rounded-md flex-shrink-0
            ${selectedFile && !isLoading && BACKEND_URL !== PLACEHOLDER_BACKEND_URL_CHECK ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-400 cursor-not-allowed'}
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50`}
        >
          {/* Button text changes based on loading state */}
          {isLoading ? 'Uploading...' : 'Upload File'}
        </button>

      </div> {/* End of flex container */}

      {/* Area to display messages (upload status, errors) */}
      {/* Only show if the 'message' state is not empty */}
      {message && (
        <p className={`mt-4 text-sm ${message.includes('successful') ? 'text-green-600' : 'text-red-500'}`}>
          {message} {/* Display the current message */}
        </p>
      )}

      {/* Show the name of the selected file before upload attempt, if a file is selected and no message is shown yet */}
      {selectedFile && !isLoading && !message && (
           <p className="mt-2 text-sm text-gray-700">Selected: <span className="font-semibold">{selectedFile.name}</span></p>
      )}

       {selectedFile && !isLoading && message.includes('successful') && (
          <p className="mt-2 text-sm text-gray-700">Uploaded: <span className="font-semibold">{selectedFile.name}</span></p>
      )}

    </div> // End of main container div
  );
}

export default FileUpload;
