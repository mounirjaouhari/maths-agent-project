#!/bin/bash

# scripts/run_migrations.sh
# Ce script exécute les migrations de base de données Alembic.
# Il est conçu pour être exécuté dans l'environnement de déploiement (ex: Kubernetes Job)
# ou en développement local.

# Arrêter le script si une commande échoue
set -e

# Chemin vers le répertoire du persistence-service
# Assurez-vous que ce chemin est correct par rapport à l'endroit où le script est exécuté
PERSISTENCE_SERVICE_DIR="./backend/persistence-service"

# Vérifier si le répertoire du service de persistance existe
if [ ! -d "$PERSISTENCE_SERVICE_DIR" ]; then
  echo "Erreur: Le répertoire du service de persistance n'existe pas: $PERSISTENCE_SERVICE_DIR"
  echo "Veuillez exécuter ce script depuis la racine du projet ou ajuster le chemin."
  exit 1
fi

echo "Début de l'exécution des migrations de base de données..."

# Naviguer vers le répertoire du persistence-service
cd "$PERSISTENCE_SERVICE_DIR"

# Activer l'environnement virtuel si Poetry est utilisé
# Si vous utilisez un venv standard, activez-le ici:
# source .venv/bin/activate
# Si Poetry est utilisé et le venv est en projet:
if command -v poetry &> /dev/null; then
  echo "Poetry détecté. Installation des dépendances et activation de l'environnement virtuel..."
  # Assurez-vous que les dépendances sont installées pour Alembic
  poetry install --no-root --only main || { echo "Erreur: Échec de l'installation des dépendances Poetry."; exit 1; }
  # Exécuter la commande Alembic via poetry run
  poetry run alembic upgrade head || { echo "Erreur: Échec de l'exécution des migrations Alembic."; exit 1; }
else
  # Si Poetry n'est pas utilisé, assurez-vous que les dépendances sont installées via pip
  echo "Poetry non détecté. Assurez-vous que les dépendances sont installées via pip."
  pip install -r requirements.txt || { echo "Erreur: Échec de l'installation des dépendances pip."; exit 1; }
  # Exécuter la commande Alembic directement
  alembic upgrade head || { echo "Erreur: Échec de l'exécution des migrations Alembic."; exit 1; }
fi

echo "Migrations de base de données terminées avec succès."

