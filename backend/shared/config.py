# backend/shared/config.py

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

# Définition de la classe de configuration en utilisant Pydantic BaseSettings
# Cela permet de charger les variables d'environnement et de les valider.
# Les variables d'environnement peuvent être préfixées par 'MATH_AGENT_'.
class Settings(BaseSettings):
    # Configuration du modèle de paramètres pour charger depuis les variables d'environnement
    # et les fichiers .env
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore", # Ignorer les variables d'environnement non définies ici
        case_sensitive=False, # Les noms de variables d'environnement ne sont pas sensibles à la casse
        # Vous pouvez ajouter un préfixe pour les variables d'environnement spécifiques à l'application
        # env_prefix="MATH_AGENT_" 
    )

    # --- Paramètres généraux de l'application ---
    APP_NAME: str = "Agent IA de Rédaction Mathématique"
    ENVIRONMENT: str = "development" # development, staging, production
    DEBUG_MODE: bool = False

    # --- Paramètres de la base de données PostgreSQL ---
    # L'URL de la base de données est sensible et doit être gérée via des secrets Kubernetes.
    # Ce champ sera rempli par la variable d'environnement injectée.
    DATABASE_URL: str 

    # --- Paramètres de la base de données Neo4j (optionnel) ---
    # Si Neo4j est utilisé pour la KB, son URL et ses identifiants
    NEO4J_URI: str = None
    NEO4J_USER: str = None
    NEO4J_PASSWORD: str = None

    # --- Paramètres Redis (pour Celery Broker et Cache) ---
    # L'URL de Redis est sensible et doit être gérée via des secrets Kubernetes.
    REDIS_URL: str 
    REDIS_PASSWORD: str = None # Mot de passe Redis, si configuré

    # --- Paramètres Celery ---
    CELERY_BROKER_URL: str 
    CELERY_RESULT_BACKEND: str 
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list[str] = ["json"]
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True
    CELERY_TASK_QUEUE_MAX_PRIORITY: int = 9 # Priorités de 0 à 9

    # --- Clés API des LLMs (sensibles, gérées via secrets) ---
    OPENAI_API_KEY: str = None
    GOOGLE_AI_API_KEY: str = None
    ANTHROPIC_API_KEY: str = None

    # --- URLs des services internes (pour la communication inter-microservices) ---
    # Ces URLs sont généralement des noms de service Kubernetes résolus en interne.
    PERSISTENCE_SERVICE_URL: str = "http://persistence-service-service:80"
    KB_SERVICE_URL: str = "http://kb-service-service:80"
    GENERATION_SERVICE_URL: str = "http://generation-service-service:80"
    QC_SERVICE_URL: str = "http://qc-service-service:80"
    INTERACTION_SERVICE_URL: str = "http://interaction-service-service:80"
    ASSEMBLY_EXPORT_SERVICE_URL: str = "http://assembly-export-service-service:80"

    # --- Paramètres de sécurité ---
    SECRET_KEY: str # Clé secrète pour le hachage de mots de passe, JWT, etc. (très sensible)
    ALGORITHM: str = "HS256" # Algorithme de signature JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # Durée de vie du jeton d'accès

    # --- Paramètres de monitoring et logging ---
    # PROMETHEUS_ENDPOINT: str = None # Exemple si un Pushgateway est utilisé
    # LOG_LEVEL: str = "INFO" # Niveau de log par défaut

    # --- Paramètres spécifiques au QC ---
    QC_MATH_VERIFIER_TOOLS_PATH: str = "/app/external_tools" # Chemin vers les exécutables des outils de vérification mathématique (ex: Z3)
    QC_VALIDATION_THRESHOLD: float = 70.0 # Score QC minimum pour la validation automatique en mode autonome

    # --- Paramètres spécifiques au Raffinement ---
    MAX_REFINEMENT_ATTEMPTS: int = 5 # Nombre maximal de tentatives de raffinement automatique

    # --- Paramètres spécifiques à l'Export ---
    PANDOC_PATH: str = "/usr/bin/pandoc" # Chemin vers l'exécutable Pandoc
    PDFLATEX_PATH: str = "/usr/bin/pdflatex" # Chemin vers l'exécutable pdflatex


# Utilisation de lru_cache pour s'assurer que les paramètres ne sont chargés qu'une seule fois
@lru_cache()
def get_settings():
    """Charge et retourne l'instance des paramètres de l'application."""
    return Settings()

