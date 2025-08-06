Guide d'Installation de TeX Live dans Docker
Ce document fournit des instructions détaillées pour l'installation et la configuration de TeX Live dans un environnement Docker. TeX Live est une distribution LaTeX complète, indispensable pour le Service Assemblage & Export afin de compiler les documents LaTeX assemblés en format PDF.

1. Description de l'Outil
TeX Live est une distribution complète du système de composition TeX, incluant LaTeX, des polices, des macros et de nombreux utilitaires. Elle est utilisée pour compiler les fichiers .tex (code source LaTeX) en documents finaux comme des PDF.

Dans le contexte de l'Agent IA, TeX Live est principalement utilisé par le assembly-export-service pour :

Compiler le fichier source LaTeX assemblé en PDF.

S'assurer que toutes les dépendances LaTeX (packages, classes de documents) sont disponibles pour une compilation réussie.

2. Prérequis
Avant d'installer TeX Live, assurez-vous que votre environnement Docker répond aux prérequis suivants :

Docker : Un environnement Docker fonctionnel est nécessaire pour construire et exécuter les images.

Connexion internet : Pour télécharger les paquets TeX Live.

Espace disque suffisant : Une installation complète de TeX Live est très volumineuse (plusieurs Go). Prévoyez un espace disque adéquat sur la machine hôte et dans l'image Docker.

3. Instructions d'Installation dans un Dockerfile
L'installation de TeX Live est recommandée directement dans le Dockerfile de l'image du worker Celery d'exportation (celery-worker-export). Cela garantit un environnement cohérent et reproductible.

Il existe plusieurs approches pour installer TeX Live dans un Dockerfile, en fonction de la taille de l'image souhaitée et des packages LaTeX spécifiques dont vous avez besoin.

3.1. Option 1 : Installation Minimale et Ajout de Packages Spécifiques (Recommandé)
Cette approche permet de réduire la taille de l'image Docker en n'installant que les packages essentiels et en ajoutant spécifiquement ceux qui sont requis par vos documents LaTeX.

# Exemple partiel de Dockerfile pour le Celery worker d'exportation
# FROM python:3.10-slim

# ... (autres installations de dépendances Python et Pandoc) ...

# Installer une distribution TeX minimale (TeX Live)
# Mettre à jour la liste des paquets et installer les composants de base de TeX Live
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        texlive-latex-base \
        texlive-fonts-recommended \
        texlive-plain-generic \
        latexmk \
        && \
    # Nettoyer le cache apt pour réduire la taille de l'image Docker
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Installer des packages LaTeX spécifiques si nécessaire (ex: amsmath, amsfonts, graphicx)
# Utilisez `tlmgr` (TeX Live Manager) si disponible et configuré, ou installez via apt-get si les packages sont disponibles.
# RUN tlmgr install amsmath amsfonts graphicx # Exemple si tlmgr est configuré
# OU
# RUN apt-get update && apt-get install -y texlive-latex-extra texlive-fonts-extra && apt-get clean && rm -rf /var/lib/apt/lists/*

# ... (le reste de votre Dockerfile) ...

Note sur tlmgr : L'utilisation de tlmgr (TeX Live Manager) dans un Dockerfile peut être complexe car il nécessite une configuration initiale et une mise à jour des dépôts TeX Live. Souvent, il est plus simple de s'appuyer sur les packages texlive-* fournis par le gestionnaire de paquets du système d'exploitation si vos besoins sont couverts.

3.2. Option 2 : Installation Complète (Déconseillé pour la taille de l'image)
Cette option installe la distribution TeX Live complète. L'image Docker résultante sera très volumineuse.

# Exemple partiel de Dockerfile pour le Celery worker d'exportation
# FROM python:3.10-slim

# ... (autres installations) ...

# Installer la distribution TeX Live complète (TRÈS GRAND!)
RUN apt-get update && \
    apt-get install -y texlive-full && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ... (le reste de votre Dockerfile) ...

4. Vérification de l'Installation
Après la construction de l'image Docker, vous pouvez vérifier que pdflatex (le compilateur principal) est correctement installé et accessible en exécutant la commande suivante dans le conteneur :

pdflatex --version

Vous devriez voir la version de pdflatex installée, par exemple :

pdfTeX 3.141592653-2.6-1.40.24 (TeX Live 2022/Debian)
kpathsea version 6.3.4
...

5. Considérations Spécifiques à l'Intégration
Taille de l'Image Docker : L'installation de TeX Live, même minimale, augmente considérablement la taille de l'image Docker. Optimisez votre Dockerfile en utilisant des builds multi-étapes si possible pour réduire la taille finale.

Packages LaTeX Manquants : Si vos documents LaTeX utilisent des packages qui ne sont pas inclus dans l'installation minimale, la compilation échouera. Vous devrez identifier ces packages et les ajouter explicitement à l'installation (voir Section 3.1).

Gestion des Erreurs de Compilation : La compilation LaTeX peut échouer pour