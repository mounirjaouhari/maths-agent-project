# Fichier placeholder pour main.py
# backend/persistence-service/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from contextlib import asynccontextmanager
import logging
import asyncio

from shared.config import get_settings
from shared.exceptions import (
    NotFoundException, BadRequestException, ConflictException,
    ServiceUnavailableException, InternalServerError
)
from .database import engine, init_db # Importe l'engine SQLAlchemy et la fonction d'initialisation DB
from .api.internal import endpoints as internal_endpoints # Importe les routeurs d'endpoints internes

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
    logger.info(f"Démarrage du Persistence Service en mode {settings.ENVIRONMENT}...")
    
    # Initialiser la base de données (créer les tables si elles n'existent pas)
    # Ceci est généralement fait par un job de migration (Alembic) en production,
    # mais peut être utile pour le développement local.
    try:
        # Tente d'initialiser la DB, si elle n'est pas déjà initialisée par Alembic
        # Note: En production, les migrations Alembic devraient gérer la création/mise à jour du schéma.
        # Cette ligne est principalement pour le développement rapide.
        await init_db() 
        logger.info("Base de données initialisée (si non déjà existante).")
    except Exception as e:
        logger.error(f"Échec de l'initialisation de la base de données: {e}")
        raise RuntimeError("Impossible d'initialiser la base de données, le service ne peut pas démarrer.")

    # Test de connexion à la base de données
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: sync_conn.execute(text("SELECT 1")))
        logger.info("Connexion à la base de données établie avec succès.")
    except Exception as e:
        logger.error(f"Échec de la connexion à la base de données au démarrage: {e}")
        raise RuntimeError("Impossible de se connecter à la base de données, le service ne peut pas démarrer.")

    yield # L'application est maintenant prête à servir les requêtes

    logger.info("Arrêt du Persistence Service...")
    # Fermer la connexion à la base de données
    await engine.dispose()
    logger.info("Connexion à la base de données fermée.")

# Initialisation de l'application FastAPI
app = FastAPI(
    title=get_settings().APP_NAME + " - Persistence Service",
    description="Service interne pour la gestion de la persistance des données.",
    version="1.0.0",
    docs_url="/docs", # URL pour la documentation OpenAPI (Swagger UI)
    redoc_url="/redoc", # URL pour la documentation ReDoc
    lifespan=lifespan # Associe le gestionnaire de contexte
)

# Inclusion des routeurs API internes
# Ces routeurs définissent les endpoints pour la communication inter-services
app.include_router(internal_endpoints.router, prefix="/internal", tags=["internal"])

# Endpoint de santé de base pour Kubernetes (liveness probe)
@app.get("/health", status_code=status.HTTP_200_OK, summary="Vérifier la santé du Persistence Service")
async def health_check():
    """
    Vérifie si le Persistence Service est en cours d'exécution et peut se connecter à la base de données.
    """
    try:
        # Tente une connexion simple à la base de données
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: sync_conn.execute(text("SELECT 1")))
        return {"status": "ok", "message": "Persistence Service is healthy and connected to DB"}
    except Exception as e:
        logger.error(f"Health check failed: Database connection error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Database connection error: {e}")

# Endpoint de préparation pour Kubernetes (readiness probe)
@app.get("/ready", status_code=status.HTTP_200_OK, summary="Vérifier la préparation du Persistence Service")
async def readiness_check():
    """
    Vérifie si le Persistence Service est prêt à recevoir du trafic.
    Doit inclure une vérification de la connexion à la base de données.
    """
    try:
        # La sonde de préparation doit être plus stricte, vérifiant que la DB est prête
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: sync_conn.execute(text("SELECT 1")))
        return {"status": "ready", "message": "Persistence Service is ready to serve requests"}
    except Exception as e:
        logger.error(f"Readiness check failed: Database not ready: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Database not ready: {e}")

# Importe text de sqlalchemy pour l'utilisation dans les requêtes brutes (pour les health checks)
from sqlalchemy import text 
