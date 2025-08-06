// frontend/src/pages/SettingsPage.js

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../api/apiService'; // Notre service API
import { FaArrowLeft, FaSave } from 'react-icons/fa';

const SettingsPage = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [username, setUsername] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Pour l'exemple, nous allons simuler un utilisateur connecté et ses paramètres.
  // En réalité, vous récupéreriez les infos de l'utilisateur via une API.
  const { data: userSettings, isLoading: isSettingsLoading, isError: isSettingsError, error: settingsError } = useQuery({
    queryKey: ['userSettings'],
    queryFn: async () => {
      // Simuler un appel API pour récupérer les paramètres de l'utilisateur
      // Dans un vrai backend, il y aurait un endpoint pour récupérer le profil utilisateur
      // const response = await apiService.getUserProfile();
      // return response;
      return {
        username: "utilisateur@example.com",
        default_level: "L2",
        default_style: "Hybride",
        notifications_enabled: true
      };
    },
    onSuccess: (data) => {
      setUsername(data.username);
      // Mettre à jour d'autres états si des préférences sont chargées
    }
  });

  // Mutation pour mettre à jour les paramètres de l'utilisateur
  const updateSettingsMutation = useMutation({
    mutationFn: async (updatedData) => {
      // Simuler un appel API pour mettre à jour les paramètres
      // await apiService.updateUserProfile(updatedData);
      console.log("Mise à jour des paramètres simulée:", updatedData);
      return updatedData;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['userSettings']); // Invalide le cache pour rafraîchir
      setSuccessMessage('Paramètres mis à jour avec succès !');
      setError('');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
    },
    onError: (err) => {
      console.error('Erreur lors de la mise à jour des paramètres:', err);
      setError(err.message || 'Échec de la mise à jour des paramètres.');
      setSuccessMessage('');
    },
  });

  const handleUpdateProfile = (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');
    // Ici, vous enverriez les données du profil (ex: username si modifiable)
    updateSettingsMutation.mutate({ username });
  };

  const handleChangePassword = (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');

    if (newPassword !== confirmNewPassword) {
      setError('Le nouveau mot de passe et sa confirmation ne correspondent pas.');
      return;
    }
    if (newPassword.length < 8) {
      setError('Le nouveau mot de passe doit contenir au moins 8 caractères.');
      return;
    }

    // Dans un vrai backend, vous appelleriez un endpoint de changement de mot de passe
    // qui vérifierait l'ancien mot de passe avant de le changer.
    updateSettingsMutation.mutate({ current_password: currentPassword, new_password: newPassword });
  };

  if (isSettingsLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <p className="text-gray-600 text-lg">Chargement des paramètres...</p>
      </div>
    );
  }

  if (isSettingsError) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-red-50">
        <p className="text-red-700 text-lg">Erreur lors du chargement des paramètres: {settingsError.message}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-lg p-8">
        <div className="flex justify-between items-center mb-6">
          <button
            onClick={() => navigate('/')}
            className="text-gray-600 hover:text-gray-800 flex items-center"
          >
            <FaArrowLeft className="mr-2" /> Retour au Tableau de Bord
          </button>
          <h1 className="text-3xl font-bold text-gray-800">Paramètres</h1>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md relative mb-4" role="alert">
            <span className="block sm:inline">{error}</span>
          </div>
        )}
        {successMessage && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-md relative mb-4" role="alert">
            <span className="block sm:inline">{successMessage}</span>
          </div>
        )}

        {/* Section Profil Utilisateur */}
        <div className="mb-8 border-b pb-6">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">Profil Utilisateur</h2>
          <form onSubmit={handleUpdateProfile} className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                Nom d'utilisateur (Email)
              </label>
              <input
                type="email"
                id="username"
                name="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="votre.email@exemple.com"
                disabled={updateSettingsMutation.isPending}
              />
            </div>
            <div>
              <button
                type="submit"
                disabled={updateSettingsMutation.isPending}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                <FaSave className="mr-2" /> {updateSettingsMutation.isPending ? 'Sauvegarde...' : 'Sauvegarder le Profil'}
              </button>
            </div>
          </form>
        </div>

        {/* Section Changement de Mot de Passe */}
        <div className="mb-8 border-b pb-6">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">Changer le Mot de Passe</h2>
          <form onSubmit={handleChangePassword} className="space-y-4">
            <div>
              <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-700">
                Mot de passe actuel
              </label>
              <input
                type="password"
                id="currentPassword"
                name="currentPassword"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="********"
                disabled={updateSettingsMutation.isPending}
              />
            </div>
            <div>
              <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700">
                Nouveau mot de passe
              </label>
              <input
                type="password"
                id="newPassword"
                name="newPassword"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength="8"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="********"
                disabled={updateSettingsMutation.isPending}
              />
            </div>
            <div>
              <label htmlFor="confirmNewPassword" className="block text-sm font-medium text-gray-700">
                Confirmer le nouveau mot de passe
              </label>
              <input
                type="password"
                id="confirmNewPassword"
                name="confirmNewPassword"
                value={confirmNewPassword}
                onChange={(e) => setConfirmNewPassword(e.target.value)}
                required
                minLength="8"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="********"
                disabled={updateSettingsMutation.isPending}
              />
            </div>
            <div>
              <button
                type="submit"
                disabled={updateSettingsMutation.isPending}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                <FaSave className="mr-2" /> {updateSettingsMutation.isPending ? 'Sauvegarde...' : 'Changer le Mot de Passe'}
              </button>
            </div>
          </form>
        </div>

        {/* Section Préférences d'Application (Exemple) */}
        <div>
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">Préférences d'Application</h2>
          {/* Exemple de préférences: niveau par défaut, style par défaut */}
          <div className="space-y-4">
            <div>
              <label htmlFor="defaultLevel" className="block text-sm font-medium text-gray-700">
                Niveau Pédagogique par Défaut
              </label>
              <select
                id="defaultLevel"
                name="defaultLevel"
                value={userSettings?.default_level || ''}
                onChange={(e) => updateSettingsMutation.mutate({ default_level: e.target.value })}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md shadow-sm"
                disabled={updateSettingsMutation.isPending}
              >
                <option value="L1">L1</option>
                <option value="L2">L2</option>
                <option value="M1">M1</option>
                <option value="M2">M2</option>
                <option value="Lycée">Lycée</option>
              </select>
            </div>
            <div>
              <label htmlFor="defaultStyle" className="block text-sm font-medium text-gray-700">
                Style de Rédaction par Défaut
              </label>
              <select
                id="defaultStyle"
                name="defaultStyle"
                value={userSettings?.default_style || ''}
                onChange={(e) => updateSettingsMutation.mutate({ default_style: e.target.value })}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md shadow-sm"
                disabled={updateSettingsMutation.isPending}
              >
                <option value="Bourbaki">Bourbaki (Formel, Rigoureux)</option>
                <option value="Feynman">Feynman (Intuitif, Pédagogique)</option>
                <option value="Hybride">Hybride (Équilibré)</option>
              </select>
            </div>
            <div className="flex items-center">
              <input
                id="notificationsEnabled"
                name="notificationsEnabled"
                type="checkbox"
                checked={userSettings?.notifications_enabled || false}
                onChange={(e) => updateSettingsMutation.mutate({ notifications_enabled: e.target.checked })}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                disabled={updateSettingsMutation.isPending}
              />
              <label htmlFor="notificationsEnabled" className="ml-2 block text-sm font-medium text-gray-700">
                Activer les notifications
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
