Glossaire Technique
Ce glossaire fournit des définitions concises des termes techniques clés utilisés dans ce guide et l'ensemble du projet de l'Agent IA de Rédaction Mathématique Double-Mode. Il vise à assurer une compréhension commune de la terminologie pour tous les membres de l'équipe de développement.

A
Agentic AI: Un système d'intelligence artificielle conçu pour agir de manière autonome ou semi-autonome afin d'atteindre des objectifs complexes, souvent en décomposant les tâches, en planifiant, en exécutant des actions et en s'adaptant en fonction des retours.

Alembic: Un outil de migration de base de données pour SQLAlchemy en Python, utilisé pour gérer les changements de schéma de base de données de manière structurée et reproductible.

API Gateway: Un point d'entrée unique pour toutes les requêtes API externes vers le backend. Il gère l'authentification, l'autorisation et le routage vers les microservices appropriés.

Asynchrone: Se réfère à des opérations qui ne bloquent pas l'exécution du programme pendant qu'elles attendent un résultat (par exemple, les appels à des APIs externes ou les tâches de longue durée).

B
Backend: La partie serveur de l'application qui gère la logique métier, l'accès aux données et la communication avec les services externes.

Base de Connaissances (KB): Une base de données structurée contenant des informations vérifiées sur un domaine spécifique (ici, les mathématiques et la pédagogie), utilisée pour ancrer et guider la génération de contenu.

Broker de Messages: Un intermédiaire (comme Redis ou RabbitMQ) qui reçoit, stocke et distribue les messages (tâches) entre les producteurs (Moteur Workflow) et les consommateurs (Workers Celery).

C
Celery: Une file d'attente de tâches distribuée en Python, utilisée pour exécuter des opérations longues de manière asynchrone via des workers dédiés.

CI/CD (Continuous Integration/Continuous Deployment): Un ensemble de pratiques et d'outils qui automatisent les étapes de build, test et déploiement du code pour permettre des livraisons fréquentes et fiables.

Conteneurisation (Docker): La pratique consistant à empaqueter une application et toutes ses dépendances dans un conteneur portable et isolé (une image Docker) pour garantir un environnement d'exécution cohérent.

CRUD: Acronyme pour Create, Read, Update, Delete, les quatre opérations de base sur les données persistantes.

D
Débit (Throughput): Une métrique mesurant le nombre de requêtes ou d'opérations qu'un système peut traiter par unité de temps.

Dette Technique: Le coût implicite des développements futurs causé par des choix techniques rapides ou non optimaux faits dans le passé.

Diagramme Entité-Relation (ERD): Une représentation visuelle de la structure d'une base de données relationnelle, montrant les tables, les colonnes et les relations.

E
End-to-End Tests (E2E): Tests qui simulent le flux utilisateur complet à travers l'application, de l'interface utilisateur au backend et aux dépendances.

F
FastAPI: Un framework web Python moderne et rapide pour construire des APIs, supportant nativement l'asynchronisme.

Frontend: La partie cliente de l'application (généralement exécutée dans un navigateur web) qui gère l'interface utilisateur et interagit avec le backend.

G
Gestion d'État: Le processus de gestion des données de l'application côté client (dans le frontend) de manière cohérente et prédictible (ex: avec Redux, Vuex, Context API).

gRPC: Un framework RPC (Remote Procedure Call) open source et performant, souvent utilisé pour la communication inter-services.

I
Ingénierie des Prompts: L'art et la science de formuler des requêtes (prompts) efficaces pour les modèles de langage afin d'obtenir les résultats souhaités.

Infrastructure as Code (IaC): La pratique consistant à gérer et provisionner l'infrastructure (serveurs, réseaux, bases de données) à l'aide de fichiers de configuration versionnés plutôt que de processus manuels.

J
JWT (JSON Web Token): Un standard sécurisé pour représenter des informations (claims) entre deux parties sous forme d'objet JSON signé. Souvent utilisé pour l'authentification et l'autorisation.

K
Kubernetes: Une plateforme open source pour automatiser le déploiement, la mise à l'échelle et la gestion des applications conteneurisées.

L
LaTeX: Un système de composition de documents largement utilisé dans le monde académique pour la production de documents techniques et scientifiques, en particulier ceux contenant des formules mathématiques.

Latence: Une métrique mesurant le temps nécessaire pour qu'un système (ou un service) réponde à une requête.

LLM (Large Language Model): Un modèle de langage basé sur des réseaux neuronaux profonds, entraîné sur de vastes quantités de texte, capable de générer du texte, de répondre à des questions, de traduire, etc.

Logging Centralisé: La pratique consistant à collecter, agréger et stocker les logs de tous les composants d'un système distribué dans un emplacement central pour faciliter l'analyse et le débogage.

M
Microservices: Une architecture logicielle où une application est structurée comme une collection de services petits, autonomes et faiblement couplés, qui communiquent via des réseaux.

Monitoring: Le processus de collecte, de stockage et de visualisation des métriques sur l'état et la performance d'une application et de son infrastructure.

N
NLU (Natural Language Understanding): Une branche du NLP qui se concentre sur la compréhension du sens et de l'intention derrière le langage humain.

O
OpenAPI (Swagger): Un standard pour décrire les APIs RESTful dans un format lisible par machine, utilisé pour la documentation, la génération de code et la validation.

Orchestration (Conteneurs): Le processus d'automatisation du déploiement, de la gestion, de la mise à l'échelle et de la mise en réseau des conteneurs.

ORM (Object-Relational Mapper): Une bibliothèque qui permet aux développeurs d'interagir avec une base de données relationnelle en utilisant des objets et des méthodes dans leur langage de programmation (ex: SQLAlchemy en Python) plutôt que d'écrire du SQL brut.

OWASP (Open Web Application Security Project): Une fondation à but non lucratif qui travaille à améliorer la sécurité des logiciels. Leur "OWASP Top 10" liste les risques de sécurité web les plus critiques.

P
Pydantic: Une bibliothèque Python pour la validation des données et la gestion des paramètres, souvent utilisée avec FastAPI.

Pyramide de Tests: Un modèle conceptuel suggérant une proportion de différents types de tests : beaucoup de tests unitaires, moins de tests d'intégration, et encore moins de tests End-to-End.

R
Raffinement: Le processus d'amélioration itérative du contenu généré par l'IA en fonction des retours (humains ou automatiques).

Redis: Une base de données clé-valeur en mémoire, souvent utilisée comme cache ou comme broker de messages pour Celery.

Réplication (Base de Données): Le processus de copie des données d'une base de données vers une ou plusieurs autres bases de données pour la redondance, la haute disponibilité ou l'amélioration des performances de lecture.

Repository Pattern: Un modèle de conception logicielle qui abstrait la logique d'accès aux données derrière une interface orientée collection.

Résilience: La capacité d'un système à se remettre rapidement des défaillances et à continuer de fonctionner.

Retries (Réessais): Le mécanisme consistant à tenter à nouveau l'exécution d'une opération (par exemple, un appel API externe) qui a échoué en raison d'une erreur transitoire.

Robustesse: La capacité d'un système à gérer les erreurs d'entrée, les conditions inattendues ou les contraintes sans se comporter de manière imprévue ou planter.

S
Scalabilité: La capacité d'un système à gérer une charge de travail croissante en augmentant les ressources.

Schéma de Base de Données: La structure formelle d'une base de données, définissant les tables, les colonnes, les types de données et les relations.

Secrets Management: Le processus de gestion sécurisée des informations sensibles (clés API, mots de passe) en utilisant des outils dédiés.

Service Level Agreement (SLA): Un accord qui définit le niveau de service attendu d'un système (par exemple, disponibilité, temps de réponse).

SQLAlchemy: Un ORM et un toolkit SQL pour Python, utilisé pour interagir avec les bases de données relationnelles.

SSL/TLS (HTTPS): Protocoles cryptographiques utilisés pour sécuriser la communication sur un réseau, garantissant la confidentialité et l'intégrité des données.

Stack Technologique: L'ensemble des technologies, frameworks, langages et outils utilisés pour construire et déployer une application.

Stratégie de Déploiement: La méthode utilisée pour mettre à jour une application en production (ex: Rolling Update, Blue/Green, Canary).

SymPy: Une bibliothèque Python pour le calcul symbolique, utilisée dans le Module QC.

T
Tolérance d'Erreur Résiduelle: Le pourcentage d'erreurs qui subsistent dans un document final après le processus de génération et de validation.

Transaction (Base de Données): Une séquence d'opérations de base de données traitées comme une seule unité atomique (tout ou rien).

U
Unit of Work (UoW): Un modèle de conception qui gère une collection d'objets affectés par une transaction et coordonne l'écriture des changements dans la base de données.

Tests d'Acceptation Utilisateur (UAT): Tests réalisés par les utilisateurs finaux pour vérifier que l'application répond à leurs besoins et exigences.

V
Vérification Formelle: L'utilisation de méthodes mathématiques pour prouver la correction d'un programme ou d'une assertion.

W
WebSockets: Un protocole de communication qui permet un canal de communication bidirectionnel persistant entre un client (navigateur) et un serveur.

Worker (Celery): Un processus qui exécute les tâches asynchrones envoyées à la file d'attente Celery.

X
XSS (Cross-Site Scripting): Une vulnérabilité web qui permet à un attaquant d'injecter des scripts malveillants dans le contenu web visualisé par d'autres utilisateurs.