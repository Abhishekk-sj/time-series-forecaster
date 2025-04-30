// frontend/src/components/ColumnSelector.js
import React, { useState, useEffect } from 'react';
import axios from 'axios'; // Import axios

// Your actual Render backend URL provided by you
const BACKEND_URL = 'https://time-series-forecaster-backend.onrender.com';

// Define the types of columns the user needs to select
const COLUMN_TYPES = ['Date Column', 'Value Column', 'Aggregation Column (Optional)'];

// Define the available forecasting frequencies
const FORECAST_FREQUENCIES = ['Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly'];


// This component receives the column headers from the backend,
// the original file data, and a function to call when the forecast results are received.
function ColumnSelector({ columnHeaders, file, onForecastComplete }) {
  // State to store the user's selected column for each type
  const [selectedColumns, setSelectedColumns] = useState({
    'Date Column': '',
    'Value Column': '',
    'Aggregation Column (Optional)': ''
  });
  // State for the selected forecasting frequency
  const [selectedFrequency, setSelectedFrequency] = useState('Daily'); // Default to Daily
  // State for the number of periods to forecast
  const [forecastPeriods, setForecastPeriods] = useState(12); // Default to 12 periods
  // State for any error message
  const [errorMessage, setErrorMessage] = useState('');
  // State to track if inputs are valid to enable the forecast button
  const [canRunForecast, setCanRunForecast] = useState(false);
  // State to track if the forecast is currently loading
  const [isLoadingForecast, setIsLoadingForecast] = useState(false);


  // Effect hook to run validation whenever inputs change
  useEffect(() => {
    // Check if the required columns (Date and Value) have been selected
    const dateSelected = selectedColumns['Date Column'] !== '';
    const valueSelected = selectedColumns['Value Column'] !== '';
     // Check if frequency is selected (should always be true with default)
    const frequencySelected = selectedFrequency !== '';
    // Check if forecastPeriods is a positive integer
    const periodsValid = Number.isInteger(forecastPeriods) && forecastPeriods > 0;


    if (dateSelected && valueSelected && frequencySelected && periodsValid) {
      // If required selections are valid, check for duplicates among required ones
      if (selectedColumns['Date Column'] === selectedColumns['Value Column']) {
         setErrorMessage('Date and Value columns cannot be the same.');
         setCanRunForecast(false);
      } else {
         // All required selections are valid
         setErrorMessage('');
         setCanRunForecast(true);
      }
    } else {
      // Required selections are incomplete or periods/frequency invalid
       if (!periodsValid) {
           setErrorMessage('Please enter a positive integer for forecast periods.');
       } else if (!frequencySelected) {
            setErrorMessage('Please select a forecasting frequency.'); // Should not happen with default
       } else {
           setErrorMessage(''); // Clear error if just incomplete selections
       }
      setCanRunForecast(false);
    }

     // Optional: Add more complex validation here if needed
      if (Object.values(selectedColumns).some(col => col !== '' && !columnHeaders.includes(col))) {
           setErrorMessage('One or more selected columns are not in the original data.');
           setCanRunForecast(false);
      }

  }, [selectedColumns, selectedFrequency, forecastPeriods, columnHeaders]); // Dependency array


  // Handle dropdown selection change for columns
  const handleSelectChange = (columnType, selectedValue) => {
    setErrorMessage('');
    setSelectedColumns(prevSelections => ({
      ...prevSelections,
      [columnType]: selectedValue
    }));
  };

   // Handle dropdown selection change for frequency
  const handleFrequencyChange = (event) => {
       setErrorMessage('');
       setSelectedFrequency(event.target.value);
  };

   // Handle forecast periods input change
  const handlePeriodsChange = (event) => {
       const value = event.target.value;
       setErrorMessage('');
       const intValue = parseInt(value, 10);
       setForecastPeriods(isNaN(intValue) ? value : intValue); // Store raw or integer value
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
     if (file) {
         formData.append('file', file); // Append the original file content
     } else {
          console.error("Original file data is missing!");
          setErrorMessage("Error: Original file data is missing.");
          setIsLoadingForecast(false);
          return;
     }

     // Append the selections and parameters as form fields
     formData.append('selectedColumns', JSON.stringify(selectedColumns)); // Selections object as JSON string
     formData.append('selectedFrequency', selectedFrequency); // <--- ADD SELECTED FREQUENCY
     formData.append('forecastPeriods', forecastPeriods.toString()); // Periods as string


     console.log(`Attempting to run forecast on: ${BACKEND_URL}/forecast`); // Debug log
     console.log('Sending FormData:', {
         filename: file.name,
         selectedColumns: selectedColumns,
         selectedFrequency: selectedFrequency,
         forecastPeriods: forecastPeriods
     }); // More detailed debug log


    try {
      // Send POST request to the backend's /forecast endpoint
      const response = await axios.post(`${BACKEND_URL}/forecast`, formData, {
         timeout: 120000 // Increased timeout (e.g., 120 seconds)
      });

      // If the request is successful (status 2xx)
      console.log('Forecast response:', response.data); // Log the response from the backend
      if (onForecastComplete) {
          onForecastComplete(response.data); // Call parent callback with results
      }

    } catch (error) {
      // Handle errors during the request
      console.error('Forecast failed:', error);
      let displayError = 'Forecasting failed.';

      if (error.response) {
        displayError = `Forecasting failed: ${error.response.status} - ${error.response.data?.error || error.response.statusText || 'Unknown Error'}`;
         // Check if backend returned specific error details
         if (error.response.data?.details) {
             displayError += ` Details: ${error.response.data.details}`;
         }
      } else if (error.request) {
        displayError = 'Forecasting failed: No response from server. Is the backend running and reachable?';
      } else {
        displayError = `Forecasting failed: ${error.message}`;
      }
       setErrorMessage(displayError); // Display the error message to the user

    } finally {
      setIsLoadingForecast(false); // Ensure loading state is false
    }
  };


  return (
    <div className="mt-8 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-semibold mb-4 text-gray-700">
        Step 2: Select Columns and Parameters
      </h2>

      <p className="mb-4 text-gray-600 text-sm">
        Identify the columns needed for forecasting, the forecast horizon, and the desired output frequency.
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

       {/* Forecasting Frequency Dropdown */}
       <div className="flex flex-col sm:flex-row items-start sm:items-center mb-4 space-y-2 sm:space-y-0 sm:space-x-4">
          <label htmlFor="forecastFrequency" className="block text-sm font-medium text-gray-700 w-40 flex-shrink-0">
             Forecast Frequency:
          </label>
           <select
             id="forecastFrequency"
             value={selectedFrequency}
             onChange={handleFrequencyChange}
             className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
           >
             {FORECAST_FREQUENCIES.map(freq => (
               <option key={freq} value={freq}>
                 {freq}
               </option>
             ))}
           </select>
       </div>


      {/* Forecast Periods Input */}
       <div className="flex flex-col sm:flex-row items-start sm:items-center mb-4 space-y-2 sm:space-y-0 sm:space-x-4">
          <label htmlFor="forecastPeriods" className="block text-sm font-medium text-gray-700 w-40 flex-shrink-0">
             Forecast Periods:
          </label>
           <input
             type="number"
             id="forecastPeriods"
             value={forecastPeriods}
             onChange={handlePeriodsChange}
             min="1"
             step="1"
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
          onClick={handleRunForecast}
          disabled={!canRunForecast || isLoadingForecast}
          className={`px-6 py-2 text-white font-semibold rounded-md
            ${canRunForecast && !isLoadingForecast ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-400 cursor-not-allowed'}
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 flex items-center`}
        >
           {isLoadingForecast && (
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            )}
          {isLoadingForecast ? 'Running Forecast...' : 'Run Forecast'}
        </button>
      </div>

    </div>
  );
}

export default ColumnSelector;
