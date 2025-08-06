# backend/workflow-service/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from contextlib import asynccontextmanager
import logging

from shared.config import get_settings
from shared.exceptions import (
    NotFoundException, BadRequestException, ServiceUnavailableException,
    InternalServerError
)
from .api.internal import endpoints as internal_endpoints # Importe les routeurs d'endpoints internes
from .tasks import workflow_tasks # Importe les tâches Celery pour s'assurer qu'elles sont découvertes
from .celery_app import celery_app # Importe l'instance Celery pour l'initialisation

# Configure le logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gestionnaire de contexte asynchrone pour les événements de démarrage et d'arrêt de l'application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Fonctions exécutées au démarrage et à l'arrêt de l'application FastAPI.
    """
    settings = get_settings()
    logger.info(f"Démarrage du Workflow Service en mode {settings.ENVIRONMENT}...")
    
    # Initialiser Celery (peut être fait ici ou dans celery_app.py)
    # S'assurer que l'application Celery est bien configurée avec le broker
    try:
        # Test de connexion au broker Celery (Redis)
        # Ceci est un test simple, une vérification plus robuste pourrait être nécessaire
        with celery_app.connection_for_url(settings.CELERY_BROKER_URL) as connection:
            connection.connect()
        logger.info("Connexion au broker Celery établie avec succès.")
    except Exception as e:
        logger.error(f"Échec de la connexion au broker Celery: {e}")
        # En production, cela pourrait empêcher l'application de démarrer ou la marquer comme non prête
        raise RuntimeError("Impossible de se connecter au broker Celery, le service ne peut pas démarrer.")

    # Ici, vous pouvez ajouter d'autres logiques de démarrage, par exemple:
    # - Initialiser des clients pour les services de persistance/KB
    
    yield # L'application est maintenant prête à servir les requêtes

    logger.info("Arrêt du Workflow Service...")
    # Ici, vous pouvez ajouter des logiques d'arrêt, par exemple:
    # - Fermer des connexions
    # - Nettoyer des ressources

# Initialisation de l'application FastAPI
app = FastAPI(
    title=get_settings().APP_NAME + " - Workflow Service",
    description="Service interne pour la gestion du workflow et l'orchestration des tâches.",
    version="1.0.0",
    docs_url="/docs", # URL pour la documentation OpenAPI (Swagger UI)
    redoc_url="/redoc", # URL pour la documentation ReDoc
    lifespan=lifespan # Associe le gestionnaire de contexte
)

# Inclusion des routeurs API internes
# Ces routeurs définissent les endpoints pour la communication inter-services
app.include_router(internal_endpoints.router, prefix="/internal", tags=["internal"])

# Endpoint de santé de base pour Kubernetes (liveness probe)
@app.get("/health", status_code=status.HTTP_200_OK, summary="Vérifier la santé du Workflow Service")
async def health_check():
    """
    Vérifie si le Workflow Service est en cours d'exécution et peut se connecter à ses dépendances critiques.
    """
    settings = get_settings()
    try:
        # Vérifier la connexion au broker Celery
        with celery_app.connection_for_url(settings.CELERY_BROKER_URL) as connection:
            connection.info() # Tente d'obtenir des informations sur la connexion
        
        # Vérifier la connexion au service de persistance (exemple)
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.PERSISTENCE_SERVICE_URL}/health")
            resp.raise_for_status() # Lève une exception si le statut n'est pas 2xx

        return {"status": "ok", "message": "Workflow Service is healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Dépendance non saine: {e}")

# Endpoint de préparation pour Kubernetes (readiness probe)
@app.get("/ready", status_code=status.HTTP_200_OK, summary="Vérifier la préparation du Workflow Service")
async def readiness_check():
    """
    Vérifie si le Workflow Service est prêt à recevoir du trafic.
    """
    settings = get_settings()
    try:
        # La sonde de préparation doit être plus stricte, vérifiant que toutes les dépendances sont prêtes
        with celery_app.connection_for_url(settings.CELERY_BROKER_URL) as connection:
            connection.info()
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.PERSISTENCE_SERVICE_URL}/ready")
            resp.raise_for_status()

        return {"status": "ready", "message": "Workflow Service is ready to serve requests"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Dépendance non prête: {e}")

