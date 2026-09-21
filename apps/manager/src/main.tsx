import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { ErrorBoundary } from './components/ErrorBoundary';
import { detectAndSetLocale } from './lib/i18n';
import './index.css';
import './design-tokens.css';

detectAndSetLocale();

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <ErrorBoundary label="Application Root">
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);
