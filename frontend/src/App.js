// frontend/src/App.js

import React from 'react';
import { Provider } from 'react-redux'; // Pour Redux
import store from './store'; // Importe le store Redux
import AppRouter from './router'; // Importe notre routeur d'application

// Composant racine de l'application React
const App = () => {
  return (
    // Le Provider Redux rend le store disponible à tous les composants enfants
    <Provider store={store}>
      <div className="min-h-screen flex flex-col bg-gray-100">
        {/* En-tête de l'application (peut être un composant séparé) */}
        <header className="bg-white shadow-sm p-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">Auto-Maths IA</h1>
          <nav>
            {/* Navigation principale (peut être un composant de navigation) */}
            {/* <Link to="/" className="text-blue-600 hover:text-blue-800 mr-4">Tableau de Bord</Link> */}
            {/* <Link to="/settings" className="text-blue-600 hover:text-blue-800">Paramètres</Link> */}
            {/* Bouton de déconnexion */}
            {/* <button onClick={handleLogout} className="text-red-500 hover:text-red-700 ml-4">Déconnexion</button> */}
          </nav>
        </header>

        {/* Contenu principal de l'application géré par le routeur */}
        <main className="flex-1">
          <AppRouter />
        </main>

        {/* Pied de page de l'application (peut être un composant séparé) */}
        <footer className="bg-gray-800 text-white text-center p-4 mt-8">
          <p>&copy; {new Date().getFullYear()} Auto-Maths IA. Tous droits réservés.</p>
        </footer>
      </div>
    </Provider>
  );
};

export default App;
