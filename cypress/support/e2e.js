// cypress/support/e2e.js
// Ce fichier est chargé avant chaque fichier de spécification de test.
// C'est un excellent endroit pour inclure des commandes personnalisées et des comportements globaux.

// Importer des commandes personnalisées si vous en avez (ex: login, createProject)
// import './commands';

// --- Configuration globale pour les tests E2E ---

// Avant chaque test, nous pourrions vouloir nettoyer la base de données ou l'état de l'application.
// Ceci est un exemple conceptuel. L'implémentation réelle dépendra de votre backend.
beforeEach(() => {
  // Optionnel: Réinitialiser la base de données ou l'état du backend avant chaque test
  // Utile pour garantir l'indépendance des tests.
  // cy.exec('npm run db:reset'); // Exemple de commande pour réinitialiser la DB via un script npm
  // cy.request('POST', `${Cypress.env('API_BASE_URL')}/test/reset-db`); // Exemple d'appel API pour réinitialiser le backend
  
  // Assurez-vous que le localStorage est propre si vous stockez des jetons là
  cy.clearLocalStorage();
});

// --- Commandes Cypress personnalisées (exemples) ---

// Commande personnalisée pour se connecter
// Utilise l'API du backend pour obtenir un jeton JWT et le stocker dans localStorage.
Cypress.Commands.add('login', (username, password) => {
  cy.request('POST', `${Cypress.env('API_BASE_URL')}/users/login`, {
    username: username,
    password: password
  }).then((response) => {
    expect(response.status).to.eq(200);
    localStorage.setItem('accessToken', response.body.access_token);
  });
});

// Commande personnalisée pour créer un projet via l'API
Cypress.Commands.add('createProjectViaApi', (projectData) => {
  cy.request({
    method: 'POST',
    url: `${Cypress.env('API_BASE_URL')}/projects`,
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
    },
    body: projectData
  }).then((response) => {
    expect(response.status).to.eq(201);
    return response.body; // Retourne l'objet projet créé
  });
});


// Commande personnalisée pour naviguer et attendre le chargement de la page
Cypress.Commands.add('visitAndWaitForPageLoad', (url) => {
  cy.visit(url);
  // Attendre que l'application React soit complètement chargée
  // Cela peut être un élément spécifique dans le DOM ou un indicateur de chargement qui disparaît
  cy.get('#root').should('be.visible'); // Assurez-vous que l'élément racine est visible
  // cy.get('.loading-spinner').should('not.exist'); // Si vous avez un spinner de chargement
});

// --- Utilitaires de test ---

// Fonction pour générer un nom d'utilisateur unique pour les tests d'enregistrement
Cypress.Commands.add('generateUniqueUsername', () => {
  const timestamp = new Date().getTime();
  return `testuser_${timestamp}@example.com`;
});

// --- Configuration des requêtes API pour éviter les CORS en local si nécessaire ---
// Si votre backend et frontend sont sur des ports différents en dev,
// et que Nginx ne gère pas le proxy en local, vous pourriez avoir besoin de ceci.
// Dans notre cas, Nginx est censé gérer le proxy pour les requêtes /v1/.
// cy.server();
// cy.route('POST', '**/v1/users/login').as('login');
// cy.route('POST', '**/v1/projects').as('createProject');

