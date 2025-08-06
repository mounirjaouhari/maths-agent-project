#!/bin/bash

# scripts/setup_dev_env.sh
# Ce script automatise la configuration de l'environnement de développement local.

# Arrêter le script si une commande échoue
set -e

echo "Démarrage de la configuration de l'environnement de développement..."

# --- 1. Vérification des prérequis ---
echo "1. Vérification des prérequis..."

command -v docker >/dev/null 2>&1 || { echo >&2 "Docker n'est pas installé. Veuillez l'installer avant de continuer. Aborting."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo >&2 "Docker Compose n'est pas installé. Veuillez l'installer avant de continuer. Aborting."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo >&2 "Python 3 n'est pas installé. Veuillez l'installer avant de continuer. Aborting."; exit 1; }
command -v yarn >/dev/null 2>&1 || { echo >&2 "Yarn n'est pas installé. Veuillez l'installer (ou utiliser npm). Aborting."; exit 1; }
command -v poetry >/dev/null 2>&1 || { echo >&2 "Poetry n'est pas installé. Veuillez l'installer (pip install poetry). Aborting."; exit 1; }

echo "Tous les prérequis sont installés."

# --- 2. Démarrage des services d'infrastructure (bases de données, broker) via Docker Compose ---
echo "2. Démarrage des services d'infrastructure via Docker Compose..."
# Ce fichier docker-compose.yml doit être créé à la racine du projet
# et inclure PostgreSQL, Redis, et potentiellement Neo4j.
# Pour l'exemple, nous allons juste simuler la commande.
# Une version complète nécessiterait un fichier docker-compose.yml réel.
echo "NOTE: Assurez-vous d'avoir un fichier docker-compose.yml à la racine du projet pour démarrer les DBs et le broker."
echo "Exécution de 'docker-compose up -d db_service_name broker_service_name'..."
# docker-compose up -d postgresql-service redis-service # Exemple de commande
echo "Services d'infrastructure démarrés (vérifiez manuellement si le docker-compose.yml n'est pas fourni)."
sleep 5 # Laisser le temps aux services de démarrer

# --- 3. Configuration du Backend (Python) ---
echo "3. Configuration des microservices Backend (Python)..."

BACKEND_SERVICES=(
  "api-gateway"
  "workflow-service"
  "persistence-service"
  "kb-service"
  "generation-service"
  "qc-service"
  "interaction-service"
  "assembly-export-service"
)

for service in "${BACKEND_SERVICES[@]}"; do
  SERVICE_PATH="./backend/$service"
  echo "  - Configuration de $service ($SERVICE_PATH)..."
  if [ -d "$SERVICE_PATH" ]; then
    cd "$SERVICE_PATH"
    # Installer Poetry et les dépendances
    poetry install --no-root || { echo "Erreur: Échec de l'installation des dépendances pour $service."; exit 1; }
    echo "    Dépendances installées pour $service."
    cd - > /dev/null # Retour au répertoire précédent
  else
    echo "    AVERTISSEMENT: Répertoire $SERVICE_PATH non trouvé. Ignoré."
  fi
done

echo "Configuration du Backend terminée."

# --- 4. Configuration du Frontend (JavaScript/React) ---
echo "4. Configuration du Frontend (JavaScript/React)..."

FRONTEND_PATH="./frontend"
if [ -d "$FRONTEND_PATH" ]; then
  cd "$FRONTEND_PATH"
  # Installer les dépendances Yarn
  yarn install --frozen-lockfile || { echo "Erreur: Échec de l'installation des dépendances Yarn pour le frontend."; exit 1; }
  echo "  Dépendances Yarn installées pour le frontend."
  cd - > /dev/null # Retour au répertoire précédent
else
  echo "  AVERTISSEMENT: Répertoire $FRONTEND_PATH non trouvé. Ignoré."
fi

echo "Configuration du Frontend terminée."

# --- 5. Exécution des migrations de base de données ---
echo "5. Exécution des migrations de base de données..."
# Exécuter le script de migrations
./scripts/run_migrations.sh || { echo "Erreur: Échec de l'exécution des migrations."; exit 1; }
echo "Migrations exécutées avec succès."

# --- 6. Peuplement initial de la Base de Connaissances ---
echo "6. Peuplement initial de la Base de Connaissances..."
# Exécuter le script de peuplement de la KB
python3 ./scripts/populate_kb.py || { echo "Erreur: Échec du peuplement de la KB."; exit 1; }
echo "Base de Connaissances peuplée avec succès."

# --- 7. Instructions pour démarrer les services ---
echo "7. Environnement de développement configuré !"
echo "Pour démarrer les services localement, vous pouvez utiliser les commandes suivantes dans des terminaux séparés:"
echo ""
echo "  # Pour le Frontend (dans le répertoire frontend/)"
echo "  cd ./frontend"
echo "  yarn start"
echo ""
echo "  # Pour chaque microservice Backend (dans son répertoire respectif, ex: backend/api-gateway/)"
echo "  # Assurez-vous que les variables d'environnement nécessaires sont chargées (ex: via un fichier .env)"
echo "  # Exemple pour l'API Gateway:"
echo "  cd ./backend/api-gateway"
echo "  poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "  # Pour les Workers Celery (dans le répertoire workflow-service/)"
echo "  # Assurez-vous que le broker Redis est accessible"
echo "  cd ./backend/workflow-service"
echo "  poetry run celery -A tasks.workflow_tasks worker -l info -Q default,generation,qc,export"
echo ""
echo "Bon développement !"

