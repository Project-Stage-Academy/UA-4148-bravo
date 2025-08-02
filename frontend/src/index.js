import ReactDOM from 'react-dom/client';
import './css/main.css';
import './index.css';
import reportWebVitals from './reportWebVitals';
import App from './components/App/app';
import React from 'react';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);

reportWebVitals();
