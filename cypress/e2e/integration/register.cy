// cypress/e2e/integration/register.cy.js
// Scénario de test End-to-End pour la page d'enregistrement.

describe('Register Page', () => {
  beforeEach(() => {
    // Visiter la page d'enregistrement avant chaque test
    cy.visit('/register'); 
  });

  it('should display register form', () => {
    // Vérifier que les éléments du formulaire d'enregistrement sont visibles
    cy.get('h1').should('contain', 'S\'enregistrer');
    cy.get('input[id="username"]').should('be.visible');
    cy.get('input[id="password"]').should('be.visible');
    cy.get('input[id="confirmPassword"]').should('be.visible');
    cy.get('button[type="submit"]').should('contain', 'S\'enregistrer');
    cy.get('button').should('contain', 'Se connecter'); // Lien vers la page de connexion
  });

  it('should show error message when passwords do not match', () => {
    // Tenter de s'enregistrer avec des mots de passe qui ne correspondent pas
    const uniqueUsername = cy.generateUniqueUsername(); // Utiliser la commande personnalisée
    cy.get('input[id="username"]').type(uniqueUsername);
    cy.get('input[id="password"]').type('password123');
    cy.get('input[id="confirmPassword"]').type('passwordABC');
    cy.get('button[type="submit"]').click();

    // Vérifier que le message d'erreur est affiché
    cy.get('[role="alert"]').should('be.visible').and('contain', 'Les mots de passe ne correspondent pas.');
  });

  it('should register a new user successfully and redirect to login', () => {
    // Tenter de s'enregistrer avec des informations valides
    const uniqueUsername = cy.generateUniqueUsername();
    const password = 'securepassword123';

    cy.get('input[id="username"]').type(uniqueUsername);
    cy.get('input[id="password"]').type(password);
    cy.get('input[id="confirmPassword"]').type(password);
    cy.get('button[type="submit"]').click();

    // Vérifier que le message de succès est affiché
    cy.get('[role="alert"]').should('be.visible').and('contain', 'Enregistrement réussi !');
    
    // Vérifier que l'URL est redirigée vers la page de connexion après un délai
    cy.url().should('include', '/login');
    cy.get('h1').should('contain', 'Connexion');
  });

  it('should show error message if username already exists', () => {
    // Pré-enregistrer un utilisateur via l'API pour le test
    const existingUsername = cy.generateUniqueUsername();
    const password = 'testpassword123';
    cy.request('POST', `${Cypress.env('API_BASE_URL')}/users/register`, { username: existingUsername, password: password });

    // Tenter de s'enregistrer avec le même nom d'utilisateur
    cy.visit('/register'); // Recharger la page pour s'assurer d'un état propre
    cy.get('input[id="username"]').type(existingUsername);
    cy.get('input[id="password"]').type(password);
    cy.get('input[id="confirmPassword"]').type(password);
    cy.get('button[type="submit"]').click();

    // Vérifier que le message d'erreur de conflit est affiché
    cy.get('[role="alert"]').should('be.visible').and('contain', 'Le nom d\'utilisateur');
    cy.get('[role="alert"]').should('be.visible').and('contain', 'existe déjà');
  });

  it('should navigate to login page', () => {
    // Cliquer sur le bouton pour naviguer vers la page de connexion
    cy.get('button').contains('Se connecter').click();
    cy.url().should('include', '/login');
    cy.get('h1').should('contain', 'Connexion');
  });
});
