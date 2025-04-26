// frontend/src/components/ColumnSelector.js
import React, { useState, useEffect } from 'react';

// Define the types of columns the user needs to select
const COLUMN_TYPES = ['Date Column', 'Value Column', 'Aggregation Column (Optional)'];

// This component receives the column headers from the backend
// and a function to call when the user confirms their selections
function ColumnSelector({ columnHeaders, onColumnsSelected }) {
  // State to store the user's selected column for each type
  // Initialized with an empty string for each required column type
  const [selectedColumns, setSelectedColumns] = useState({
    'Date Column': '',
    'Value Column': '',
    'Aggregation Column (Optional)': ''
  });
  // State to store any error message related to selections
  const [selectionError, setSelectionError] = useState('');
  // State to track if the selections are valid to enable the button
  const [canProceed, setCanProceed] = useState(false);

  // Effect hook to run validation whenever selectedColumns state changes
  useEffect(() => {
    // Check if the required columns (Date and Value) have been selected
    const dateSelected = selectedColumns['Date Column'] !== '';
    const valueSelected = selectedColumns['Value Column'] !== '';

    if (dateSelected && valueSelected) {
      // If required columns are selected, check for duplicates among required ones
      if (selectedColumns['Date Column'] === selectedColumns['Value Column']) {
         setSelectionError('Date and Value columns cannot be the same.');
         setCanProceed(false);
      } else {
         // Selections are valid
         setSelectionError('');
         setCanProceed(true);
      }
    } else {
      // Required columns are not yet selected
      setSelectionError(''); // Clear error if selections become incomplete
      setCanProceed(false);
    }

     // Optional: Add more complex validation here if needed (e.g., check if selected columns exist in headers)
      if (Object.values(selectedColumns).some(col => col !== '' && !columnHeaders.includes(col))) {
           setSelectionError('One or more selected columns are not in the original data.');
           setCanProceed(false);
      }


  }, [selectedColumns, columnHeaders]); // Dependency array: rerun when selectedColumns or columnHeaders change

  // Function called when a dropdown selection changes
  const handleSelectChange = (columnType, selectedValue) => {
    // Update the state for the specific column type that changed
    setSelectedColumns(prevSelections => ({
      ...prevSelections, // Copy existing selections
      [columnType]: selectedValue // Update the value for the changed column type
    }));
    // Validation will run automatically via the useEffect hook
  };

  // Function called when the user clicks the "Proceed" button
  const handleProceed = () => {
    // Perform final validation before proceeding
    if (canProceed) {
      // Call the parent component's callback function, passing the selections
      onColumnsSelected(selectedColumns);
    } else {
       // Should not happen if button is disabled, but good fallback
       setSelectionError('Please complete the required column selections.');
    }
  };


  return (
    // Main container div with Tailwind styling
    <div className="mt-8 p-6 bg-white rounded-lg shadow-md">
      {/* Section Title */}
      <h2 className="text-2xl font-semibold mb-4 text-gray-700">
        Step 2: Select Columns
      </h2>

      {/* Instruction for the user */}
      <p className="mb-4 text-gray-600 text-sm">
        Please identify the date column, the value column you want to forecast, and an optional aggregation column from your uploaded data.
      </p>

      {/* Mapping over the defined column types to create a dropdown for each */}
      {COLUMN_TYPES.map(type => (
        // Container for each selection row
        <div key={type} className="flex flex-col sm:flex-row items-start sm:items-center mb-4 space-y-2 sm:space-y-0 sm:space-x-4">
          {/* Label for the dropdown - uses Tailwind for styling */}
          <label className="block text-sm font-medium text-gray-700 w-40 flex-shrink-0">
            {type}: {/* Display the column type (e.g., "Date Column:") */}
          </label>

          {/* Dropdown (Select) Element */}
          <select
            // Value of the select is controlled by our state
            value={selectedColumns[type]}
            // onChange calls our handler, passing the column type and the new selected value
            onChange={(e) => handleSelectChange(type, e.target.value)}
            // Tailwind classes for styling the select dropdown
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
          >
            {/* Default disabled option */}
            <option value="" disabled>
              Select a column
            </option>
            {/* Map over the column headers received from the backend to create options */}
            {columnHeaders.map(header => (
              // Each header becomes an option in the dropdown
              <option key={header} value={header}>
                {header} {/* Display the header name */}
              </option>
            ))}
          </select>
        </div>
      ))}

      {/* Display validation error message if selectionError state is not empty */}
      {selectionError && (
         <p className="mt-4 text-sm text-red-500">{selectionError}</p>
      )}


      {/* Proceed Button */}
      <div className="mt-6 flex justify-end">
        <button
          onClick={handleProceed} // Calls our handler when clicked
          disabled={!canProceed} // Button is disabled unless selections are valid
          // Tailwind classes for button styling, conditional styling based on disabled state
          className={`px-6 py-2 text-white font-semibold rounded-md
            ${canProceed ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-400 cursor-not-allowed'}
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50`}
        >
          Select Columns and Proceed
        </button>
      </div>

    </div> // End of main container div
  );
}

export default ColumnSelector; // Export the component for use in App.js
