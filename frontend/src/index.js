// frontend/src/index.js
import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles/index.css'; // Import your Tailwind CSS file
import App from './App'; // Import your main App component

// Find the root element in index.html and create a React root
const container = document.getElementById('root');
const root = ReactDOM.createRoot(container);

// Render the main App component into the root
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Optional: You can remove the web-vitals import and call if you removed the dependency
// import reportWebVitals from './reportWebVitals';
// reportWebVitals();
