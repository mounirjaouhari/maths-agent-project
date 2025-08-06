// frontend/src/pages/DashboardPage.js

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../api/apiService';
import { FaPlus, FaFolderOpen, FaArchive, FaTrash } from 'react-icons/fa';

// Composant Modal de confirmation/alerte personnalisé
const ConfirmationModal = ({ message, onConfirm, onCancel, type = 'confirm' }) => {
  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-11/12 md:w-1/3">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          {type === 'confirm' ? 'Confirmation' : 'Notification'}
        </h3>
        <p className="text-gray-700 mb-6">{message}</p>
        <div className="flex justify-end space-x-3">
          {type === 'confirm' && (
            <button
              onClick={onCancel}
              className="px-4 py-2 bg-gray-300 text-gray-800 rounded-md hover:bg-gray-400 transition-colors"
            >
              Annuler
            </button>
          )}
          <button
            onClick={onConfirm}
            className={`px-4 py-2 rounded-md transition-colors ${
              type === 'confirm' ? 'bg-red-500 text-white hover:bg-red-600' : 'bg-blue-500 text-white hover:bg-blue-600'
            }`}
          >
            {type === 'confirm' ? 'Confirmer' : 'OK'}
          </button>
        </div>
      </div>
    </div>
  );
};


const DashboardPage = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [filterStatus, setFilterStatus] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [modalConfig, setModalConfig] = useState({});

  // Requête pour récupérer la liste des projets
  const { data: projects, isLoading, isError, error } = useQuery({
    queryKey: ['projects', filterStatus],
    queryFn: () => apiService.getProjects(filterStatus),
  });

  // Mutation pour la suppression d'un projet
  const deleteProjectMutation = useMutation({
    mutationFn: (projectId) => apiService.deleteProject(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries(['projects']);
      setModalConfig({
        message: 'Projet supprimé avec succès.',
        type: 'alert',
        onConfirm: () => setShowModal(false),
      });
      setShowModal(true);
    },
    onError: (err) => {
      console.error('Erreur lors de la suppression du projet:', err);
      setModalConfig({
        message: `Échec de la suppression du projet: ${err.message || 'Erreur inconnue'}`,
        type: 'alert',
        onConfirm: () => setShowModal(false),
      });
      setShowModal(true);
    },
  });

  // Mutation pour l'archivage d'un projet
  const archiveProjectMutation = useMutation({
    mutationFn: ({ projectId, status }) => apiService.updateProject(projectId, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries(['projects']);
      setModalConfig({
        message: 'Statut du projet mis à jour avec succès.',
        type: 'alert',
        onConfirm: () => setShowModal(false),
      });
      setShowModal(true);
    },
    onError: (err) => {
      console.error('Erreur lors de la mise à jour du projet:', err);
      setModalConfig({
        message: `Échec de la mise à jour du projet: ${err.message || 'Erreur inconnue'}`,
        type: 'alert',
        onConfirm: () => setShowModal(false),
      });
      setShowModal(true);
    },
  });


  const handleCreateNewProject = () => {
    // Redirige vers la page de création de projet (à implémenter)
    navigate('/create-project');
  };

  const handleOpenProject = (projectId) => {
    navigate(`/projects/${projectId}`);
  };

  const handleDeleteProject = (projectId) => {
    setModalConfig({
      message: 'Êtes-vous sûr de vouloir supprimer ce projet ? Cette action est irréversible.',
      type: 'confirm',
      onConfirm: () => {
        deleteProjectMutation.mutate(projectId);
        setShowModal(false);
      },
      onCancel: () => setShowModal(false),
    });
    setShowModal(true);
  };

  const handleArchiveProject = (projectId) => {
    setModalConfig({
      message: 'Êtes-vous sûr de vouloir archiver ce projet ? Il ne sera plus modifiable directement.',
      type: 'confirm',
      onConfirm: () => {
        archiveProjectMutation.mutate({ projectId, status: 'archived' });
        setShowModal(false);
      },
      onCancel: () => setShowModal(false),
    });
    setShowModal(true);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <p className="text-gray-600 text-lg">Chargement des projets...</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-red-50">
        <p className="text-red-700 text-lg">Erreur lors du chargement des projets: {error.message}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-7xl mx-auto bg-white rounded-xl shadow-lg p-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-800">Mes Projets de Rédaction</h1>
          <button
            onClick={handleCreateNewProject}
            className="flex items-center px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-semibold rounded-lg shadow-md hover:from-blue-600 hover:to-indigo-700 transition-all duration-300 transform hover:scale-105"
          >
            <FaPlus className="mr-2" /> Nouveau Projet
          </button>
        </div>

        {/* Filtre de statut */}
        <div className="mb-6">
          <label htmlFor="statusFilter" className="block text-sm font-medium text-gray-700 mb-2">Filtrer par statut:</label>
          <select
            id="statusFilter"
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md shadow-sm"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="">Tous les statuts</option>
            <option value="draft">Brouillon</option>
            <option value="in_progress">En cours</option>
            <option value="completed">Terminé</option>
            <option value="archived">Archivé</option>
            <option value="error">Erreur</option>
          </select>
        </div>

        {projects.length === 0 ? (
          <div className="text-center py-10 text-gray-600">
            <p className="text-lg">Vous n'avez pas encore de projets.</p>
            <p className="mt-2">Cliquez sur "Nouveau Projet" pour commencer à rédiger !</p>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg shadow-md">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Titre
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Sujet
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Niveau
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Mode
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Statut
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Modifié le
                  </th>
                  <th scope="col" className="relative px-6 py-3">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {projects.map((project) => (
                  <tr key={project.project_id} className="hover:bg-gray-50 transition-colors duration-150">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {project.title}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {project.subject}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {project.level}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {project.mode}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                        ${project.status === 'completed' ? 'bg-green-100 text-green-800' :
                           project.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                           project.status === 'draft' ? 'bg-gray-100 text-gray-800' :
                           project.status === 'archived' ? 'bg-yellow-100 text-yellow-800' :
                           'bg-red-100 text-red-800'}`}>
                        {project.status} {project.current_step ? `- ${project.current_step}` : ''}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {new Date(project.updated_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleOpenProject(project.project_id)}
                          className="text-indigo-600 hover:text-indigo-900 flex items-center p-2 rounded-md hover:bg-indigo-50 transition-colors"
                          title="Ouvrir le projet"
                        >
                          <FaFolderOpen className="mr-1" /> Ouvrir
                        </button>
                        {project.status !== 'archived' && project.status !== 'completed' && (
                          <button
                            onClick={() => handleArchiveProject(project.project_id)}
                            className="text-yellow-600 hover:text-yellow-900 flex items-center p-2 rounded-md hover:bg-yellow-50 transition-colors"
                            title="Archiver le projet"
                            disabled={archiveProjectMutation.isPending}
                          >
                            <FaArchive className="mr-1" /> Archiver
                          </button>
                        )}
                        <button
                          onClick={() => handleDeleteProject(project.project_id)}
                          className="text-red-600 hover:text-red-900 flex items-center p-2 rounded-md hover:bg-red-50 transition-colors"
                          title="Supprimer le projet"
                          disabled={deleteProjectMutation.isPending}
                        >
                          <FaTrash className="mr-1" /> Supprimer
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showModal && (
        <ConfirmationModal
          message={modalConfig.message}
          onConfirm={modalConfig.onConfirm}
          onCancel={modalConfig.onCancel}
          type={modalConfig.type}
        />
      )}
    </div>
  );
};

export default DashboardPage;
