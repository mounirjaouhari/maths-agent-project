Agent IA de Rédaction Mathématique Double-Mode
Introduction
Ce projet vise à développer un Agent IA intelligent capable de générer du contenu mathématique (définitions, théorèmes, preuves, exercices) avec une grande précision et une pertinence pédagogique. L'agent fonctionne en deux modes principaux :

Mode Supervisé : L'IA génère du contenu étape par étape, et le professeur valide ou fournit un feedback à chaque itération.

Mode Autonome : L'IA génère des sections complètes de manière autonome, s'auto-évalue (Contrôle Qualité) et se raffine de manière itérative, avec des points de contrôle pour une révision globale.

L'objectif est de réduire considérablement le temps et l'effort nécessaires à la création de manuels, de cours ou d'exercices de mathématiques, tout en garantissant une qualité scientifique et pédagogique élevée.

Architecture Générale
L'application est construite sur une architecture de microservices pour garantir la scalabilité, la résilience et la maintenabilité. Les principaux services incluent :

API Gateway : Point d'entrée unique pour toutes les requêtes externes (authentification, routage).

Workflow Service : Le moteur d'orchestration central qui gère le cycle de vie des projets et des blocs de contenu en fonction du mode choisi.

Persistence Service : Gère toutes les opérations CRUD avec la base de données PostgreSQL pour les données des utilisateurs, projets, documents, etc.

KB Service (Base de Connaissances) : Fournit un accès structuré aux connaissances mathématiques et pédagogiques vérifiées.

Generation Service : Gère l'ingénierie des prompts, la sélection dynamique des LLM et l'interaction avec les APIs des modèles de langage externes.

QC Service (Contrôle Qualité) : Évalue la justesse mathématique, la pertinence pédagogique et la cohérence du contenu généré.

Interaction Service : Analyse le feedback utilisateur et les rapports QC pour formuler des instructions de raffinement.

Assembly & Export Service : Assemble les blocs de contenu validés et exporte le document final dans divers formats (PDF, LaTeX, Markdown).

Celery Workers : Exécutent les tâches asynchrones de longue durée (génération, QC, export).

Stack Technologique
Backend : Python (FastAPI), SQLAlchemy, Celery, Redis, PostgreSQL.

Frontend : React.js, Tailwind CSS, TipTap (éditeur de texte riche), KaTeX (rendu LaTeX), React Query, Redux Toolkit.

Bases de Données : PostgreSQL (principale), Redis (cache, broker Celery), Neo4j (pourrait être utilisée pour la KB).

Conteneurisation : Docker.

Orchestration : Kubernetes (avec Kustomize pour la gestion des environnements).

CI/CD : GitHub Actions.

Tests : Pytest (Backend), Cypress (Frontend E2E).

Démarrage Rapide (Développement Local)
Assurez-vous d'avoir Docker, Docker Compose, Python 3.10+, Node.js 18+, Yarn (ou npm) et Poetry installés.

Cloner le dépôt :

git clone https://github.com/your-repo/math-agent-project.git
cd math-agent-project

Configurer les variables d'environnement :
Créez un fichier .env à la racine de chaque sous-répertoire backend/<service-name>/ et dans frontend/.
Référez-vous aux fichiers .env.example respectifs pour les variables nécessaires.
Pour le frontend, renommez frontend/.env.example en frontend/.env.
Pour les services backend, vous devrez définir DATABASE_URL, REDIS_URL, CELERY_BROKER_URL, CELERY_RESULT_BACKEND, SECRET_KEY, et les clés API des LLM.

Démarrer les services d'infrastructure (PostgreSQL, Redis) :
Vous aurez besoin d'un fichier docker-compose.yml à la racine du projet pour démarrer ces services. (Non fourni dans cette arborescence, mais essentiel).

# Exemple de commande si docker-compose.yml existe
docker-compose up -d postgresql-service redis-service

Exécuter le script de configuration de l'environnement :
Ce script installera les dépendances Python et JavaScript, exécutera les migrations de base de données et peuplera la KB.

./scripts/setup_dev_env.sh

Démarrer les microservices Backend :
Dans des terminaux séparés, naviguez vers chaque répertoire de service et lancez-le :

# Exemple pour l'API Gateway
cd backend/api-gateway
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Répétez pour workflow-service, persistence-service, kb-service, generation-service, qc-service, interaction-service, assembly-export-service
# Pour les workers Celery (dans backend/workflow-service):
cd backend/workflow-service
poetry run celery -A tasks.workflow_tasks worker -l info -Q default,generation,qc,export

Démarrer le Frontend :

cd frontend
yarn start # ou npm start

L'application sera accessible à http://localhost:3000.

Tests
Tests Unitaires/Intégration Backend :

cd backend/<service-name>
poetry run pytest

Tests E2E Frontend (Cypress) :

cd frontend
yarn cypress open # Pour l'interface graphique Cypress
# ou
yarn cypress run # Pour l'exécution en ligne de commande

Tests Spécifiques au Domaine :

cd tests/domain_specific
poetry run pytest

Déploiement
Le déploiement est géré via Kubernetes et Kustomize.

Construire les images Docker pour chaque service.

Appliquer les manifestes Kubernetes (après avoir configuré les secrets et les Ingress pour votre cluster) :

# Pour staging
kubectl apply -k kubernetes/staging/
# Pour production
kubectl apply -k kubernetes/prod/

Documentation
Guide Technique Complet : docs/technical-guide/

Spécifications API (OpenAPI, gRPC) : docs/api-specs/

Schémas de Base de Données (ERD) : docs/kb-schema/

Templates de Prompts : docs/prompts/

Méthodologie et Résultats de Benchmarking : docs/benchmarks/

Glossaire Technique : docs/glossary.md

Ce README.md fournit une vue d'ensemble complète du projet.