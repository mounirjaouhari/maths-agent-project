// frontend/src/main.js

import React from 'react';
import ReactDOM from 'react-dom/client'; // Importe createRoot de react-dom/client
import App from './App'; // Importe le composant racine de l'application

// Trouve l'élément DOM où l'application React sera montée
const rootElement = document.getElementById('root');

// Crée une racine de rendu React
const root = ReactDOM.createRoot(rootElement);

// Rend le composant App dans la racine
// StrictMode est un outil pour identifier les problèmes potentiels dans une application.
// Il n'active aucune fonctionnalité visible dans l'UI. Il active des avertissements et des vérifications supplémentaires pour ses descendants.
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

