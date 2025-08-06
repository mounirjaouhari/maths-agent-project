# frontend/Dockerfile

# --- Étape 1: Build de l'application React ---
FROM node:18-alpine AS builder

# Définit le répertoire de travail dans le conteneur
WORKDIR /app

# Copie les fichiers de configuration du projet et les dépendances
COPY package.json ./
COPY yarn.lock ./ # Ou package-lock.json si vous utilisez npm

# Installe les dépendances
# Utiliser 'yarn install --frozen-lockfile' pour Yarn ou 'npm ci' pour npm
RUN yarn install --frozen-lockfile

# Copie le reste du code source de l'application
COPY . .

# Compile l'application React pour la production
# La commande 'build' est définie dans package.json
RUN yarn build

# --- Étape 2: Serveur Nginx pour les fichiers statiques ---
FROM nginx:alpine

# Copie la configuration Nginx personnalisée (si vous en avez une)
# Sinon, Nginx utilisera sa configuration par défaut
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Supprime la configuration par défaut de Nginx pour éviter les conflits si vous copiez la vôtre
RUN rm /etc/nginx/conf.d/default.conf

# Copie les fichiers statiques compilés depuis l'étape 'builder'
# Le chemin '/app/build' est le répertoire de sortie par défaut pour create-react-app
COPY --from=builder /app/build /usr/share/nginx/html

# Copie une configuration Nginx simple pour servir l'application SPA
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose le port par défaut de Nginx
EXPOSE 80

# Commande par défaut pour démarrer Nginx (déjà intégrée dans l'image Nginx)
CMD ["nginx", "-g", "daemon off;"]

