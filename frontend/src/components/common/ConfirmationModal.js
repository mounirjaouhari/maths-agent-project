// frontend/src/components/common/ConfirmationModal.js

import React from 'react';

const ConfirmationModal = ({ message, onConfirm, onCancel, type = 'confirm', title = '' }) => {
  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50 animate-fade-in">
      <div className="bg-white rounded-lg shadow-xl p-6 w-11/12 md:w-1/3 transform scale-95 animate-scale-in">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          {title || (type === 'confirm' ? 'Confirmation' : 'Notification')}
        </h3>
        <p className="text-gray-700 mb-6">{message}</p>
        <div className="flex justify-end space-x-3">
          {type === 'confirm' && (
            <button
              onClick={onCancel}
              className="px-4 py-2 bg-gray-300 text-gray-800 rounded-md hover:bg-gray-400 transition-colors duration-200 shadow-sm"
            >
              Annuler
            </button>
          )}
          <button
            onClick={onConfirm}
            className={`px-4 py-2 rounded-md transition-colors duration-200 shadow-sm ${
              type === 'confirm' ? 'bg-red-500 text-white hover:bg-red-600' : 'bg-blue-500 text-white hover:bg-blue-600'
            }`}
          >
            {type === 'confirm' ? 'Confirmer' : 'OK'}
          </button>
        </div>
      </div>

      {/* Styles d'animation Tailwind CSS (à ajouter dans un fichier CSS global ou via PostCSS) */}
      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes scaleIn {
          from { transform: scale(0.95); opacity: 0.8; }
          to { transform: scale(1); opacity: 1; }
        }
        .animate-fade-in {
          animation: fadeIn 0.3s ease-out forwards;
        }
        .animate-scale-in {
          animation: scaleIn 0.3s ease-out forwards;
        }
      `}</style>
    </div>
  );
};

export default ConfirmationModal;
