// frontend/src/components/ForecastResults.js
import React from 'react';
// Import necessary components and elements from react-chartjs-2 and chart.js
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
} from 'chart.js';
import 'chartjs-adapter-date-fns'; // Adapter for date-fns

// Register the necessary Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

// Define the options for the chart (can be customized further)
const chartOptions = {
  responsive: true,
  maintainAspectRatio: false, // Allow chart to adjust height more freely
  plugins: {
    legend: {
      position: 'top',
    },
    title: {
      display: true,
      text: 'Time Series Forecast Comparison', // Updated chart title
    },
    tooltip: {
        mode: 'index',
        intersect: false
    }
  },
  scales: {
    x: {
      type: 'time',
      time: {
        unit: 'day', // This will be overridden by data frequency but is a default
        tooltipFormat: 'MMM dd, yyyy',
        displayFormats: {
             day: 'MMM dd, yyyy',
             week: 'MMM dd, yyyy', // Add formats for other frequencies
             month: 'MMM yyyy',
             quarter: 'qqq yyyy',
             year: 'yyyy'
        }
      },
      title: {
         display: true,
         text: 'Date'
      },
       adapters: { // Ensure the date adapter is linked to the time scale
          date: {
              // Options for date-fns adapter if needed
          }
       }
    },
    y: {
      title: {
        display: true,
        text: 'Value'
      },
       beginAtZero: true // Start Y axis at zero (often good for value data)
    }
  },
   hover: {
       mode: 'index',
       intersect: false
   }
};


// This component receives the results with historical data and multiple model forecasts
function ForecastResults({ results }) {
  // Check if results data is available and structured as expected
  if (!results || !results.historicalData || !Array.isArray(results.historicalData) || !results.modelResults || typeof results.modelResults !== 'object') {
    return <div className="mt-8 text-red-500">Error: Invalid forecast results data structure received.</div>;
  }

  const historicalData = results.historicalData; // List of {Date, Value}
  const modelResults = results.modelResults; // Object like { "ARIMA": {...}, "ETS": {...}, ... }
  const bestMethod = results.bestMethod; // String name of the best method

  // Prepare data for Chart.js
  const datasets = [];

  // 1. Add Historical Data Dataset
  if (historicalData && historicalData.length > 0) {
      const historicalLabels = historicalData.map(item => new Date(item.Date));
      const historicalValues = historicalData.map(item => item.Value);

      datasets.push({
          label: 'Historical Data',
          data: historicalValues.map((value, index) => ({ x: historicalLabels[index], y: value })), // Format for time scale
          borderColor: 'rgba(54, 162, 235, 1)', // Blue color
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          borderWidth: 2,
          pointRadius: 3, // Show points for historical data
          fill: false,
          tension: 0.1
      });
  }

  // 2. Add Datasets for Each Model's Forecast
  const modelColors = { // Define colors for different models
       'ARIMA': 'rgba(75, 192, 192, 1)', // Greenish
       'ETS': 'rgba(255, 159, 64, 1)', // Orange
       'SMA': 'rgba(153, 102, 255, 1)' // Purple
       // Add more colors if more models are added
  };

  // Sort model names alphabetically or in a preferred order for consistent display
  const sortedModelNames = Object.keys(modelResults).sort();


  sortedModelNames.forEach(methodName => {
      const modelData = modelResults[methodName];

      // Skip if model data is missing or has an error
      if (!modelData || !Array.isArray(modelData.forecast_data) || modelData.error) {
          console.warn(`Skipping forecast display for ${methodName}: Data missing or error present.`, modelData?.error);
          return; // Skip this model
      }

      const forecastPoints = modelData.forecast_data;

      if (forecastPoints.length > 0) {
           const forecastLabels = forecastPoints.map(item => new Date(item.Date));
           const forecastValues = forecastPoints.map(item => item.ForecastValue);
           const lowerBounds = forecastPoints.map(item => item.LowerBound);
           const upperBound = forecastPoints.map(item => item.UpperBound);

           const isBestMethod = methodName === bestMethod;
           const color = modelColors[methodName] || 'rgba(128, 128, 128, 1)'; // Default to gray if color not defined

           // Add the forecast line for the model
           datasets.push({
               label: `${methodName} Forecast` + (isBestMethod ? ' (Best)' : ''), // Label includes method name
               data: forecastValues.map((value, index) => ({ x: forecastLabels[index], y: value })), // Format for time scale
               borderColor: color,
               backgroundColor: color.replace('1)', '0.2)'), // Semi-transparent background color
               borderWidth: isBestMethod ? 3 : 2, // Thicker line for the best method
               pointRadius: isBestMethod ? 4 : 2, // Larger points for the best method
               fill: false,
               tension: 0.1
           });

           // Add Confidence Interval lines ONLY for the Best Method (to avoid clutter)
           if (isBestMethod && lowerBounds && upperBound && lowerBounds.length === forecastPoints.length && upperBound.length === forecastPoints.length) {
                const ciColor = color.replace('1)', '0.5)'); // Slightly more transparent color for CI lines
               datasets.push({
                   label: `${methodName} Lower Bound (95% CI)`,
                   data: lowerBounds.map((value, index) => ({ x: forecastLabels[index], y: value })),
                   borderColor: ciColor,
                   backgroundColor: ciColor.replace('0.5)', '0.2)'), // Fill color (matches upper bound)
                   borderWidth: 1,
                   borderDash: [5, 5], // Dashed line
                   pointRadius: 0,
                   fill: '+1', // Fill the area between this dataset and the next (+1)
                   tension: 0.1
               });
               datasets.push({
                   label: `${methodName} Upper Bound (95% CI)`,
                   data: upperBound.map((value, index) => ({ x: forecastLabels[index], y: value })),
                   borderColor: ciColor,
                   backgroundColor: ciColor.replace('0.5)', '0.2)'), // Fill color
                   borderWidth: 1,
                   borderDash: [5, 5], // Dashed line
                   pointRadius: 0,
                   fill: '-1', // Fill the area between this dataset and the previous one (-1)
                   tension: 0.1
               });
           }
      } else {
           console.warn(`Skipping forecast display for ${methodName}: No forecast points received.`);
      }
  });

  const chartData = {
    datasets: datasets // Array of all datasets (historical + models + CIs)
  };


   // Find the forecast data for the best method to display in the table
   const bestMethodData = modelResults[bestMethod]?.forecast_data || [];
   const bestMethodRMSE = modelResults[bestMethod]?.evaluation_rmse || "N/A";

  return (
    <div className="mt-8 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-semibold mb-4 text-gray-700">
        Forecasting Results
      </h2>

       {/* Best Method and Evaluation Info */}
       <div className="mb-6 text-gray-700">
           <p className="text-lg font-semibold mb-2">Best Method: <span className="text-blue-600">{bestMethod}</span></p>
           <h3 className="text-xl font-semibold mb-3">Model Evaluation (RMSE)</h3>
           <ul className="list-disc list-inside ml-4">
               {/* Display RMSE for each model */}
               {sortedModelNames.map(methodName => {
                   const evalRMSE = modelResults[methodName]?.evaluation_rmse;
                   const error = modelResults[methodName]?.error;
                   return (
                       <li key={methodName} className="text-sm text-gray-600">
                           {methodName}: {error ? `Error: ${error}` : (evalRMSE !== "N/A" ? evalRMSE.toFixed(2) : "N/A (Evaluation Skipped)")}
                       </li>
                   );
               })}
           </ul>
       </div>


      {/* Chart Container */}
      <div className="mb-6" style={{ height: '400px' }}> {/* Give chart container a fixed height */}
        <Line options={chartOptions} data={chartData} />
      </div>

      {/* Table to display forecast data (Best Method Only) */}
      {bestMethodData.length > 0 && (
           <div className="mt-8">
              <h3 className="text-xl font-semibold mb-3 text-gray-700">{bestMethod} Forecast Data Table</h3>
              <div className="overflow-x-auto">
                 <table className="min-w-full divide-y divide-gray-200">
                   <thead className="bg-gray-50">
                     <tr>
                       <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                       <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{bestMethod} Forecast Value</th> {/* Dynamic header */}
                       <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Lower Bound (95% CI)</th>
                       <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Upper Bound (95% CI)</th>
                     </tr>
                   </thead>
                   <tbody className="bg-white divide-y divide-gray-200">
                     {/* Map over the best method's forecast data */}
                     {bestMethodData.map((item, index) => (
                       <tr key={index}>
                         <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.Date}</td>
                         <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.ForecastValue.toFixed(2)}</td>
                         <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.LowerBound.toFixed(2)}</td>
                         <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.UpperBound.toFixed(2)}</td>
                       </tr>
                     ))}
                   </tbody>
                 </table>
              </div>
           </div>
      )}

        {/* Message if best method data is not available */}
        {bestMethodData.length === 0 && modelResults[bestMethod]?.error && (
            <p className="mt-4 text-sm text-red-500">Could not display forecast data for the best method ({bestMethod}) due to an error: {modelResults[bestMethod].error}</p>
        )}
         {bestMethodData.length === 0 && !modelResults[bestMethod]?.error && (
             <p className="mt-4 text-sm text-gray-600">No forecast data available for the best method ({bestMethod}).</p>
         )}


    </div>
  );
}

export default ForecastResults;
