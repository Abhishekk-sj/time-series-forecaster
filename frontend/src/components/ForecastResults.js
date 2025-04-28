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
  TimeScale // Important for time series charts
  // Add other scales/elements as needed, like RadialLinearScale, ArcElement etc.
} from 'chart.js';
// Import adapters for date handling in charts if needed
import 'chartjs-adapter-date-fns'; // Adapter for date-fns (common choice)

// Register the necessary Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale // Register TimeScale
);

// Define the options for the chart
const chartOptions = {
  responsive: true, // Chart will resize with its container
  plugins: {
    legend: {
      position: 'top', // Position the legend at the top
    },
    title: {
      display: true, // Display the chart title
      text: 'Time Series Forecast', // Chart title text
    },
    tooltip: { // Configure tooltips (hover information)
        mode: 'index', // Show tooltips for all items at the same index
        intersect: false // Tooltips show even if not directly over a data point
    }
  },
  scales: { // Configure the chart axes
    x: {
      type: 'time', // Use time scale for the x-axis
      time: {
        unit: 'day', // Display unit on the time scale (e.g., 'day', 'month')
        tooltipFormat: 'MMM dd, yyyy', // Format of date displayed in tooltips
        displayFormats: { // Format of dates displayed on the axis labels
             day: 'MMM dd, yyyy',
             month: 'MMM yyyy',
             year: 'yyyy'
        }
      },
      title: {
         display: true,
         text: 'Date'
      }
    },
    y: {
      title: {
        display: true,
        text: 'Value' // Title for the y-axis
      }
    }
  },
  // Interaction options for hover/tooltip
   hover: {
       mode: 'index',
       intersect: false
   }
};


// This component receives the forecast results data from App.js
function ForecastResults({ results }) {
  // Check if results data is available and structured as expected
  if (!results || !results.forecastResults || !Array.isArray(results.forecastResults)) {
    return <div className="mt-8 text-red-500">Error: Invalid forecast results data.</div>;
  }

  const forecastData = results.forecastResults;

  // Assume we might also receive historical data later, but for now, only use forecast data for the chart
  // We need to format the data for Chart.js
  const labels = forecastData.map(item => new Date(item.Date)); // Dates for the x-axis (as Date objects)
  const forecastValues = forecastData.map(item => item.ForecastValue); // Forecasted values for the line
  const lowerBounds = forecastData.map(item => item.LowerBound); // Lower bounds for the confidence interval
  const upperBound = forecastData.map(item => item.UpperBound); // Upper bounds for the confidence interval

  // Data structure for Chart.js
  const chartData = {
    labels: labels, // X-axis labels (dates)
    datasets: [
      // Dataset for the forecast line
      {
        label: 'Forecast', // Label for the dataset in the legend
        data: forecastValues, // The data points
        borderColor: 'rgba(75, 192, 192, 1)', // Line color
        backgroundColor: 'rgba(75, 192, 192, 0.2)', // Fill color (optional)
        borderWidth: 2, // Line width
        fill: false, // Do not fill area under the line
        tension: 0.1, // Slight curve to the line
        pointRadius: 3 // Size of data points
      },
      // Dataset for the confidence interval (using a combined approach or separate lines)
      // A common way is to use two lines and fill between them.
      {
          label: 'Lower Bound (95% CI)',
          data: lowerBounds,
          borderColor: 'rgba(255, 99, 132, 0.5)', // Color for the lower bound line
          backgroundColor: 'rgba(255, 99, 132, 0.2)', // Fill color for interval (matches upper bound)
          borderWidth: 1,
          borderDash: [5, 5], // Dashed line
          pointRadius: 0, // No points for interval lines
          fill: '+1', // Fill the area between this dataset and the next (+1)
          tension: 0.1
      },
      {
          label: 'Upper Bound (95% CI)',
          data: upperBound,
          borderColor: 'rgba(255, 99, 132, 0.5)', // Color for the upper bound line
          backgroundColor: 'rgba(255, 99, 132, 0.2)', // Fill color for interval
          borderWidth: 1,
          borderDash: [5, 5], // Dashed line
          pointRadius: 0,
          fill: '-1', // Fill the area between this dataset and the previous one (-1)
          tension: 0.1
      }
       // TODO: Add historical data dataset here later if backend returns it
       // {
       //    label: 'Historical Data',
       //    data: historicalData, // Need historical data from backend
       //    borderColor: 'rgba(54, 162, 235, 1)',
       //    backgroundColor: 'rgba(54, 162, 235, 0.2)',
       //    borderWidth: 2,
       //    pointRadius: 3,
       //    fill: false,
       //    tension: 0.1
       // }
    ],
  };

  return (
    // Container div for the results section
    <div className="mt-8 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-semibold mb-4 text-gray-700">
        Forecasting Results
      </h2>

      {/* Chart Container */}
      <div className="mb-6">
        {/* Render the Line chart component */}
        <Line options={chartOptions} data={chartData} />
      </div>

      {/* Optional: Table to display forecast data */}
      <div className="mt-8">
         <h3 className="text-xl font-semibold mb-3 text-gray-700">Forecast Data Table</h3>
         <div className="overflow-x-auto"> {/* Make table scrollable on smaller screens */}
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Forecast Value</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Lower Bound (95% CI)</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Upper Bound (95% CI)</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {/* Map over the forecast data array to create table rows */}
                {forecastData.map((item, index) => (
                  <tr key={index}> {/* Use index as key, assuming data order is stable */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.Date}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.ForecastValue.toFixed(2)}</td> {/* Format value */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.LowerBound.toFixed(2)}</td> {/* Format value */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.UpperBound.toFixed(2)}</td> {/* Format value */}
                  </tr>
                ))}
              </tbody>
            </table>
         </div>
      </div>


    </div> // End of results container div
  );
}

export default ForecastResults; // Export the component
