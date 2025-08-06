// frontend/src/router/index.js

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Importez vos composants de page ici
import DashboardPage from '../pages/DashboardPage';
import ProjectEditorPage from '../pages/ProjectEditorPage';
// import SettingsPage from '../pages/SettingsPage'; // À créer si nécessaire
// import NotFoundPage from '../pages/NotFoundPage'; // À créer si nécessaire
// import LoginPage from '../pages/LoginPage'; // À créer si nécessaire
// import RegisterPage from '../pages/RegisterPage'; // À créer si nécessaire

const AppRouter = () => {
  return (
    <Router>
      <Routes>
        {/* Route pour la page de connexion (si séparée) */}
        {/* <Route path="/login" element={<LoginPage />} /> */}
        {/* <Route path="/register" element={<RegisterPage />} /> */}

        {/* Route pour le tableau de bord des projets */}
        <Route path="/" element={<DashboardPage />} />

        {/* Route pour la page de création de projet (si séparée) */}
        {/* <Route path="/create-project" element={<CreateProjectPage />} /> */}

        {/* Route pour la page d'édition d'un projet spécifique */}
        <Route path="/projects/:projectId" element={<ProjectEditorPage />} />

        {/* Route pour la page des paramètres (si séparée) */}
        {/* <Route path="/settings" element={<SettingsPage />} /> */}

        {/* Route pour la page 404 (non trouvée) */}
        {/* <Route path="*" element={<NotFoundPage />} /> */}
      </Routes>
    </Router>
  );
};

export default AppRouter;
