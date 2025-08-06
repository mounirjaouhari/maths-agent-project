// frontend/src/pages/CreateProjectPage.js

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../api/apiService'; // Notre service API
import { FaArrowLeft } from 'react-icons/fa';

const CreateProjectPage = () => {
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState('');
  const [level, setLevel] = useState('L1'); // Default value
  const [style, setStyle] = useState('Hybride'); // Default value
  const [mode, setMode] = useState('Supervisé'); // Default value
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Mutation for creating a new project
  const createProjectMutation = useMutation({
    mutationFn: (newProjectData) => apiService.createProject(newProjectData),
    onSuccess: (data) => {
      queryClient.invalidateQueries(['projects']); // Invalidate projects list cache
      alert('Projet créé avec succès !'); // Replace with custom modal later
      navigate(`/projects/${data.project_id}`); // Redirect to the new project's editor page
    },
    onError: (err) => {
      console.error('Error creating project:', err);
      setError(err.message || 'Failed to create project. Please try again.');
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');
    createProjectMutation.mutate({ title, subject, level, style, mode });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
      <div className="bg-white rounded-xl shadow-lg p-8 w-full max-w-md">
        <div className="flex justify-between items-center mb-6">
          <button
            onClick={() => navigate('/')}
            className="text-gray-600 hover:text-gray-800 flex items-center"
          >
            <FaArrowLeft className="mr-2" /> Retour au Tableau de Bord
          </button>
          <h1 className="text-3xl font-bold text-gray-800">Nouveau Projet</h1>
        </div>
        
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md relative mb-4" role="alert">
            <span className="block sm:inline">{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700">
              Titre du Projet
            </label>
            <input
              type="text"
              id="title"
              name="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="Ex: Introduction à l'Algèbre Linéaire"
            />
          </div>

          <div>
            <label htmlFor="subject" className="block text-sm font-medium text-gray-700">
              Sujet Mathématique
            </label>
            <input
              type="text"
              id="subject"
              name="subject"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="Ex: Analyse, Algèbre, Géométrie"
            />
          </div>

          <div>
            <label htmlFor="level" className="block text-sm font-medium text-gray-700">
              Niveau Pédagogique
            </label>
            <select
              id="level"
              name="level"
              value={level}
              onChange={(e) => setLevel(e.target.value)}
              required
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md shadow-sm"
            >
              <option value="L1">L1</option>
              <option value="L2">L2</option>
              <option value="M1">M1</option>
              <option value="M2">M2</option>
              <option value="Lycée">Lycée</option>
            </select>
          </div>

          <div>
            <label htmlFor="style" className="block text-sm font-medium text-gray-700">
              Style de Rédaction
            </label>
            <select
              id="style"
              name="style"
              value={style}
              onChange={(e) => setStyle(e.target.value)}
              required
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md shadow-sm"
            >
              <option value="Bourbaki">Bourbaki (Formel, Rigoureux)</option>
              <option value="Feynman">Feynman (Intuitif, Pédagogique)</option>
              <option value="Hybride">Hybride (Équilibré)</option>
            </select>
          </div>

          <div>
            <label htmlFor="mode" className="block text-sm font-medium text-gray-700">
              Mode de Fonctionnement
            </label>
            <select
              id="mode"
              name="mode"
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              required
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md shadow-sm"
            >
              <option value="Supervisé">Supervisé (Validation humaine à chaque étape)</option>
              <option value="Autonome">Autonome (Génération continue, points de contrôle)</option>
            </select>
          </div>

          <div>
            <button
              type="submit"
              disabled={createProjectMutation.isPending}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            >
              {createProjectMutation.isPending ? 'Création en cours...' : 'Créer le Projet'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateProjectPage;
