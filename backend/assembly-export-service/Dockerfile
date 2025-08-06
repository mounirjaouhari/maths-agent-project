# backend/assembly-export-service/Dockerfile

# Utilise une image de base Python légère
FROM python:3.10-slim-buster

# Définit le répertoire de travail dans le conteneur
WORKDIR /app

# Copie le fichier de dépendances et installe les dépendances Python
# Utilise --no-cache-dir pour éviter de stocker le cache pip dans l'image finale
# Utilise --upgrade pip pour s'assurer que pip est à jour
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie le code source de l'application Assembly Export Service
# Le répertoire 'shared' est copié car il contient des modules partagés
COPY . /app
COPY ../shared /app/shared

# Expose le port sur lequel l'application FastAPI écoute
EXPOSE 8000

# Commande pour démarrer l'application avec Uvicorn
# Le module 'main' se trouve à la racine de WORKDIR (/app)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

