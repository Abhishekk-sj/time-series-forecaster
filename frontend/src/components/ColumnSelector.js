// frontend/src/components/ColumnSelector.js
import React, { useState, useEffect } from 'react';
import axios from 'axios'; // Import axios

// Your actual Render backend URL provided by you
const BACKEND_URL = 'https://time-series-forecaster-backend.onrender.com';

// Define the types of columns the user needs to select
const COLUMN_TYPES = ['Date Column', 'Value Column', 'Aggregation Column (Optional)'];

// This component receives the column headers from the backend
// It also receives the original file data and a function to call
// when the forecast results are received.
function ColumnSelector({ columnHeaders, file, onForecastComplete }) { // Added 'file' and 'onForecastComplete' props
  // State to store the user's selected column for each type
  const [selectedColumns, setSelectedColumns] = useState({
    'Date Column': '',
    'Value Column': '',
    'Aggregation Column (Optional)': ''
  });
  // State for the number of periods to forecast
  const [forecastPeriods, setForecastPeriods] = useState(12); // Default to 12 periods
  // State for any error message related to selections or forecasting
  const [errorMessage, setErrorMessage] = useState(''); // Renamed selectionError to errorMessage
  // State to track if selections are valid to enable the forecast button
  const [canRunForecast, setCanRunForecast] = useState(false); // Renamed canProceed
  // State to track if the forecast is currently loading
  const [isLoadingForecast, setIsLoadingForecast] = useState(false);

  // Effect hook to run validation whenever selectedColumns or forecastPeriods change
  useEffect(() => {
    // Check if the required columns (Date and Value) have been selected
    const dateSelected = selectedColumns['Date Column'] !== '';
    const valueSelected = selectedColumns['Value Column'] !== '';
    // Check if forecastPeriods is a positive integer
    const periodsValid = Number.isInteger(forecastPeriods) && forecastPeriods > 0;


    if (dateSelected && valueSelected && periodsValid) {
      // If required columns and periods are valid, check for duplicates among required ones
      if (selectedColumns['Date Column'] === selectedColumns['Value Column']) {
         setErrorMessage('Date and Value columns cannot be the same.');
         setCanRunForecast(false);
      } else {
         // All required selections are valid
         setErrorMessage('');
         setCanRunForecast(true);
      }
    } else {
      // Required selections are not yet complete or periods invalid
      // Clear error if selections become incomplete, but keep period error if applicable
       if (!periodsValid) {
           setErrorMessage('Please enter a positive integer for forecast periods.');
       } else {
           setErrorMessage(''); // Clear error if selections are just incomplete
       }
      setCanRunForecast(false);
    }

     // Optional: Add more complex validation here if needed
      if (Object.values(selectedColumns).some(col => col !== '' && !columnHeaders.includes(col))) {
           setErrorMessage('One or more selected columns are not in the original data.');
           setCanRunForecast(false);
      }

  }, [selectedColumns, forecastPeriods, columnHeaders]); // Dependency array

  // Function called when a dropdown selection changes
  const handleSelectChange = (columnType, selectedValue) => {
    setErrorMessage(''); // Clear any previous errors on new selection
    setSelectedColumns(prevSelections => ({
      ...prevSelections,
      [columnType]: selectedValue
    }));
  };

   // Function called when the forecast periods input changes
  const handlePeriodsChange = (event) => {
       const value = event.target.value;
       setErrorMessage(''); // Clear error on input change
       // Attempt to convert to integer, but store the raw value temporarily
       const intValue = parseInt(value, 10);

       // Store the number (or NaN if invalid)
       setForecastPeriods(isNaN(intValue) ? value : intValue);

  };


  // Function called when the "Run Forecast" button is clicked
  const handleRunForecast = async () => {
    // Perform final validation before proceeding
    if (!canRunForecast) {
       setErrorMessage('Please complete valid selections and periods.');
       return;
    }

     setIsLoadingForecast(true); // Set loading state
     setErrorMessage(''); // Clear previous errors

     // Prepare data to send to backend
     const formData = new FormData();
     // Append the original file content
     if (file) { // Ensure file exists
         formData.append('file', file);
     } else {
          console.error("Original file data is missing!");
          setErrorMessage("Error: Original file data is missing.");
          setIsLoadingForecast(false);
          return;
     }

     // Append the selected columns and forecast periods as form fields (JSON stringified)
     formData.append('selectedColumns', JSON.stringify(selectedColumns));
     formData.append('forecastPeriods', forecastPeriods.toString());


     console.log(`Attempting to run forecast on: ${BACKEND_URL}/forecast`); // Debug log

    try {
      // Use axios to send a POST request to the backend's /forecast endpoint
      const response = await axios.post(`${BACKEND_URL}/forecast`, formData, {
         // axios sets Content-Type: multipart/form-data automatically with FormData
         timeout: 60000 // Increase timeout for forecasting (e.g., 60 seconds)
      });

      // If the request is successful (status 2xx)
      console.log('Forecast response:', response.data); // Log the response from the backend
      // Call the parent component's callback function, passing the results
      if (onForecastComplete) {
          onForecastComplete(response.data);
      }

    } catch (error) {
      // If there's an error during the request
      console.error('Forecast failed:', error); // Log the error
      let displayError = 'Forecasting failed.';

      if (error.response) {
        displayError = `Forecasting failed: ${error.response.status} - ${error.response.data?.error || error.response.statusText || 'Unknown Error'}`;
      } else if (error.request) {
        displayError = 'Forecasting failed: No response from server.';
      } else {
        displayError = `Forecasting failed: ${error.message}`;
      }
       setErrorMessage(displayError); // Display the error message to the user

    } finally {
      setIsLoadingForecast(false); // Set loading state back to false
    }
  };


  return (
    <div className="mt-8 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-semibold mb-4 text-gray-700">
        Step 2: Select Columns and Parameters
      </h2>

      <p className="mb-4 text-gray-600 text-sm">
        Identify the columns needed for forecasting and set the forecast horizon.
      </p>

      {/* Column Selection Dropdowns */}
      {COLUMN_TYPES.map(type => (
        <div key={type} className="flex flex-col sm:flex-row items-start sm:items-center mb-4 space-y-2 sm:space-y-0 sm:space-x-4">
          <label className="block text-sm font-medium text-gray-700 w-40 flex-shrink-0">
            {type}:
          </label>
          <select
            value={selectedColumns[type]}
            onChange={(e) => handleSelectChange(type, e.target.value)}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
          >
            <option value="" disabled>
              Select a column
            </option>
            {columnHeaders.map(header => (
              <option key={header} value={header}>
                {header}
              </option>
            ))}
          </select>
        </div>
      ))}

      {/* Forecast Periods Input */}
       <div className="flex flex-col sm:flex-row items-start sm:items-center mb-4 space-y-2 sm:space-y-0 sm:space-x-4">
          <label htmlFor="forecastPeriods" className="block text-sm font-medium text-gray-700 w-40 flex-shrink-0">
             Forecast Periods:
          </label>
           <input
             type="number" // Use type number
             id="forecastPeriods"
             value={forecastPeriods} // Controlled by state
             onChange={handlePeriodsChange} // Calls our handler
             min="1" // Minimum periods should be 1
             step="1" // Allow only integer steps
             className="mt-1 block w-full pl-3 pr-3 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
           />
       </div>


      {/* Display error message */}
      {errorMessage && (
         <p className="mt-4 text-sm text-red-500">{errorMessage}</p>
      )}


      {/* Run Forecast Button */}
      <div className="mt-6 flex justify-end">
        <button
          onClick={handleRunForecast} // Calls our handler when clicked
          disabled={!canRunForecast || isLoadingForecast} // Button disabled based on validation and loading state
          className={`px-6 py-2 text-white font-semibold rounded-md
            ${canRunForecast && !isLoadingForecast ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-400 cursor-not-allowed'}
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 flex items-center`} // Added flex and items-center for loading spinner
        >
          {/* Show loading spinner if loading */}
           {isLoadingForecast && (
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            )}
          {/* Button text changes based on loading state */}
          {isLoadingForecast ? 'Running Forecast...' : 'Run Forecast'}
        </button>
      </div>

    </div>
  );
}

export default ColumnSelector;
