// cypress/e2e/integration/login.cy.js
// Scénario de test End-to-End pour la page de connexion.

describe('Login Page', () => {
  beforeEach(() => {
    // Visiter la page de connexion avant chaque test
    cy.visit('/login'); 
  });

  it('should display login form', () => {
    // Vérifier que les éléments du formulaire de connexion sont visibles
    cy.get('h1').should('contain', 'Connexion');
    cy.get('input[id="username"]').should('be.visible');
    cy.get('input[id="password"]').should('be.visible');
    cy.get('button[type="submit"]').should('contain', 'Se connecter');
    cy.get('button').should('contain', 'S\'enregistrer'); // Lien vers la page d'enregistrement
  });

  it('should show error message on invalid credentials', () => {
    // Tenter de se connecter avec des identifiants invalides
    cy.get('input[id="username"]').type('invalid@example.com');
    cy.get('input[id="password"]').type('wrongpassword');
    cy.get('button[type="submit"]').click();

    // Vérifier que le message d'erreur est affiché
    cy.get('[role="alert"]').should('be.visible').and('contain', 'Échec de la connexion');
  });

  it('should log in with valid credentials and redirect to dashboard', () => {
    // Utiliser la commande personnalisée 'login' pour se connecter
    // Assurez-vous d'avoir un utilisateur valide dans votre backend de test
    const validUsername = Cypress.env('TEST_USERNAME'); // Récupérer depuis cypress.json env
    const validPassword = Cypress.env('TEST_PASSWORD'); // Récupérer depuis cypress.json env

    cy.get('input[id="username"]').type(validUsername);
    cy.get('input[id="password"]').type(validPassword);
    cy.get('button[type="submit"]').click();

    // Vérifier que l'URL est redirigée vers le tableau de bord
    cy.url().should('eq', Cypress.config().baseUrl + '/');
    // Vérifier qu'un élément du tableau de bord est visible (ex: le titre "Mes Projets")
    cy.get('h1').should('contain', 'Mes Projets');
  });

  it('should navigate to register page', () => {
    // Cliquer sur le bouton pour naviguer vers la page d'enregistrement
    cy.get('button').contains('S\'enregistrer').click();
    cy.url().should('include', '/register');
    cy.get('h1').should('contain', 'S\'enregistrer');
  });
});
