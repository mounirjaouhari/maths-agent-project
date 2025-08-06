// frontend/src/pages/NotFoundPage.js

import React from 'react';
import { Link } from 'react-router-dom';
import { FaExclamationCircle } from 'react-icons/fa';

const NotFoundPage = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
      <div className="bg-white rounded-xl shadow-lg p-8 text-center max-w-md w-full">
        <FaExclamationCircle className="text-red-500 text-6xl mx-auto mb-6" />
        <h1 className="text-4xl font-bold text-gray-800 mb-4">404 - Page Non Trouvée</h1>
        <p className="text-gray-700 mb-6">
          Désolé, la page que vous recherchez n'existe pas ou a été déplacée.
        </p>
        <Link 
          to="/" 
          className="inline-flex items-center px-6 py-3 bg-indigo-600 text-white font-semibold rounded-lg shadow-md hover:bg-indigo-700 transition-colors duration-200"
        >
          Retour au Tableau de Bord
        </Link>
      </div>
    </div>
  );
};

export default NotFoundPage;
