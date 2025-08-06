Configuration des Outils Externes et APIs LLM
Ce répertoire contient des guides détaillés pour l'installation et la configuration de tous les outils externes et des APIs des Modèles de Langage Avancés (LLMs) dont l'Agent IA de Rédaction Mathématique dépend.

Objectif
L'objectif de cette section est de fournir des instructions claires et reproductibles pour :

Installer les outils de calcul formel et symbolique (ex: Z3, SymPy, Wolfram Alpha) utilisés par le Service QC.

Installer les outils de conversion de documents (ex: Pandoc, distributions TeX comme TeX Live) utilisés par le Service Assemblage & Export.

Configurer l'accès aux APIs des Modèles de Langage Avancés (ex: OpenAI, Google AI/Gemini, Anthropic) utilisées par le Service Génération.

Une configuration correcte de ces dépendances externes est cruciale pour le bon fonctionnement, la performance et la fiabilité de l'Agent IA.

Contenu
Vous trouverez ici des guides spécifiques pour chaque outil ou API :

pandoc_install.md : Guide d'installation de Pandoc.

texlive_docker.md : Guide d'installation de TeX Live dans un environnement Docker.

z3_install.md : (À créer) Guide d'installation du solveur SMT Z3.

wolfram_alpha_api_config.md : (À créer) Guide de configuration de l'API Wolfram Alpha.

openai_api_config.md : (À créer) Guide de configuration de l'API OpenAI.

google_ai_api_config.md : (À créer) Guide de configuration de l'API Google AI (Gemini).

anthropic_api_config.md : (À créer) Guide de configuration de l'API Anthropic (Claude).

Utilisation
Ces guides sont destinés aux développeurs et aux équipes DevOps. Ils doivent être consultés lors de la mise en place des environnements de développement, de staging et de production, en particulier lors de la création des images Docker pour les workers Celery qui dépendent de ces outils.

Il est recommandé de suivre les instructions pour l'installation dans les Dockerfiles afin de garantir la cohérence des environnements.