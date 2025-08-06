# Fichier placeholder pour pandoc_install.md
Guide d'Installation de Pandoc
Ce document fournit des instructions détaillées pour l'installation et la configuration de Pandoc. Pandoc est un convertisseur de documents universel crucial pour le Service Assemblage & Export, utilisé pour convertir les documents LaTeX en divers formats de sortie.

1. Description de l'Outil
Pandoc est un outil en ligne de commande qui permet de convertir des documents d'un format à un autre. Il supporte une large gamme de formats d'entrée (Markdown, reStructuredText, HTML, LaTeX, Docx, etc.) et de formats de sortie (HTML, PDF, EPUB, Docx, LaTeX, Markdown, etc.).

Dans le contexte de l'Agent IA, Pandoc est principalement utilisé par le assembly-export-service pour :

Convertir le LaTeX assemblé en Markdown.

Convertir le LaTeX assemblé en HTML (potentiellement comme étape intermédiaire pour certains formats Wiki).

Gérer la conversion des formules mathématiques dans les formats cibles.

2. Prérequis
Avant d'installer Pandoc, assurez-vous que votre environnement répond aux prérequis suivants :

Système d'exploitation : Compatible avec Pandoc (Linux, macOS, Windows). Pour les déploiements Kubernetes, cela signifie généralement une image de base Linux (ex: Debian/Ubuntu).

Accès administrateur : Pour installer les paquets système.

Connexion internet : Pour télécharger les paquets nécessaires.

3. Instructions d'Installation
L'installation de Pandoc est recommandée directement dans le Dockerfile de l'image du worker Celery d'exportation (celery-worker-export). Cela garantit un environnement cohérent et reproductible.

3.1. Installation via Gestionnaire de Paquets (Recommandé pour Dockerfiles Linux)
Pour les distributions basées sur Debian/Ubuntu (comme python:3.10-slim que nous utilisons), vous pouvez installer Pandoc en utilisant apt-get.

# Exemple partiel de Dockerfile pour le Celery worker d'exportation
# FROM python:3.10-slim

# ... (autres installations de dépendances Python) ...

# Installer Pandoc
# Mettre à jour la liste des paquets et installer pandoc
RUN apt-get update && \
    apt-get install -y pandoc && \
    # Nettoyer le cache apt pour réduire la taille de l'image Docker
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ... (le reste de votre Dockerfile) ...

3.2. Vérification de l'Installation
Après l'installation, vous pouvez vérifier que Pandoc est correctement installé et accessible en exécutant la commande suivante dans le terminal (ou dans le conteneur Docker) :

pandoc --version

Vous devriez voir la version de Pandoc installée, par exemple :

pandoc 2.19.2
Compiled with pandoc-types 1.22.5, Text.Citeproc 0.7, Skylighting 0.8.6,
  citeproc-lua 0.8, LuaTeX 1.13.0, ...

4. Considérations Spécifiques à l'Intégration
Chemin d'accès : Assurez-vous que l'exécutable pandoc est dans le PATH du conteneur Docker, ce qui est généralement le cas lors d'une installation via un gestionnaire de paquets.

Rendu Mathématique : Lorsque vous convertissez du LaTeX vers des formats comme Markdown ou HTML qui doivent afficher des formules mathématiques, Pandoc peut être configuré pour utiliser des moteurs de rendu comme MathJax ou KaTeX. Le assembly-export-service devra spécifier ces options lors de l'appel à Pandoc.

# Exemple d'appel Pandoc pour convertir LaTeX en Markdown avec rendu MathJax
pandoc input.tex -o output.md --mathml --webtex # ou --mathjax

Fichiers Temporaires : Pandoc peut générer des fichiers temporaires. Le assembly-export-service doit gérer les répertoires de travail temporaires pour les conversions.

Gestion des Erreurs : Les erreurs de conversion (ex: LaTeX mal formé, formats non supportés) doivent être