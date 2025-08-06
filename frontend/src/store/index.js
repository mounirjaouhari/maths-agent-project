# Fichier placeholder pour index.js
// frontend/src/store/index.js

import { configureStore } from '@reduxjs/toolkit';
// Importez vos reducers (slices) ici
// import authReducer from './modules/auth';
// import projectReducer from './modules/projects';
// import uiReducer from './modules/ui';

// Configuration du store Redux
const store = configureStore({
  reducer: {
    // Ajoutez vos reducers ici
    // auth: authReducer,
    // projects: projectReducer,
    // ui: uiReducer,
    // Pour l'instant, un reducer vide ou un placeholder
    placeholder: (state = {}, action) => state, 
  },
  // Redux Toolkit inclut redux-thunk par défaut et gère les dev tools
  // middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(myCustomMiddleware),
  // devTools: process.env.NODE_ENV !== 'production', // Active les Redux DevTools en développement
});

export default store;

