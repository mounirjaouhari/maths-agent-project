# Fichier placeholder pour main.py
# backend/kb-service/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from contextlib import asynccontextmanager
import logging
import httpx
import redis.asyncio as redis # Utilise le client Redis asynchrone

from shared.config import get_settings
from shared.exceptions import (
    NotFoundException, BadRequestException, ServiceUnavailableException,
    InternalServerError
)
from .api.internal import endpoints as internal_endpoints # Importe les routeurs d'endpoints internes
# Si la KB est en PostgreSQL, importez la base de données SQLAlchemy
# from ..persistence-service.database import engine as pg_engine, init_db as pg_init_db
# Si la KB est en Neo4j, importez son client
# from neo4j import AsyncGraphDatabase

# Configure le logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variable globale pour le client Redis
redis_client: Optional[redis.Redis] = None

# Gestionnaire de contexte asynchrone pour les événements de démarrage et d'arrêt de l'application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Fonctions exécutées au démarrage et à l'arrêt de l'application FastAPI.
    """
    settings = get_settings()
    logger.info(f"Démarrage du KB Service en mode {settings.ENVIRONMENT}...")
    
    # Initialisation de la connexion à Redis
    try:
        global redis_client
        redis_client = redis.from_url(settings.REDIS_URL, password=settings.REDIS_PASSWORD, decode_responses=True)
        await redis_client.ping()
        logger.info("Connexion à Redis établie avec succès.")
    except Exception as e:
        logger.error(f"Échec de la connexion à Redis: {e}")
        raise RuntimeError("Impossible de se connecter à Redis, le service ne peut pas démarrer.")

    # Initialisation de la connexion à la base de données de la KB (PostgreSQL ou Neo4j)
    try:
        if "postgresql" in settings.KB_DATABASE_URL:
            # Logique pour PostgreSQL (si la KB est mappée sur la même DB que Persistence, ou une DB dédiée)
            # await pg_init_db() # Si c'est une DB PostgreSQL dédiée pour la KB
            # Test de connexion simple
            async with httpx.AsyncClient() as client:
                # Supposons que le service de persistance gère la DB PostgreSQL
                resp = await client.get(f"{settings.PERSISTENCE_SERVICE_URL}/health")
                resp.raise_for_status()
            logger.info("Connexion à la base de données PostgreSQL de la KB établie avec succès.")
        elif "neo4j" in settings.KB_DATABASE_URL:
            # Logique pour Neo4j
            # driver = AsyncGraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))
            # await driver.verify_connectivity()
            # app.state.neo4j_driver = driver # Stocker le driver dans l'état de l'app
            logger.info("Connexion à la base de données Neo4j de la KB établie avec succès.")
        else:
            logger.warning("Aucune configuration de base de données KB reconnue (PostgreSQL ou Neo4j).")
    except Exception as e:
        logger.error(f"Échec de la connexion à la base de données de la KB: {e}")
        raise RuntimeError("Impossible de se connecter à la base de données de la KB, le service ne peut pas démarrer.")

    yield # L'application est maintenant prête à servir les requêtes

    logger.info("Arrêt du KB Service...")
    # Fermeture des connexions
    if redis_client:
        await redis_client.close()
        logger.info("Connexion Redis fermée.")
    # if "neo4j" in settings.KB_DATABASE_URL and app.state.neo4j_driver:
    #     await app.state.neo4j_driver.close()
    #     logger.info("Connexion Neo4j fermée.")
    # if "postgresql" in settings.KB_DATABASE_URL and pg_engine:
    #     await pg_engine.dispose()
    #     logger.info("Connexion PostgreSQL de la KB fermée.")


# Initialisation de l'application FastAPI
app = FastAPI(
    title=get_settings().APP_NAME + " - KB Service",
    description="Service interne pour la gestion et l'accès à la Base de Connaissances mathématique et pédagogique.",
    version="1.0.0",
    docs_url="/docs", # URL pour la documentation OpenAPI (Swagger UI)
    redoc_url="/redoc", # URL pour la documentation ReDoc
    lifespan=lifespan # Associe le gestionnaire de contexte
)

# Inclusion des routeurs API internes
app.include_router(internal_endpoints.router, prefix="/internal", tags=["internal"])

# Endpoint de santé de base pour Kubernetes (liveness probe)
@app.get("/health", status_code=status.HTTP_200_OK, summary="Vérifier la santé du KB Service")
async def health_check():
    """
    Vérifie si le KB Service est en cours d'exécution et peut se connecter à ses dépendances critiques (DB, Redis).
    """
    settings = get_settings()
    try:
        # Vérifier la connexion Redis
        if redis_client:
            await redis_client.ping()
        else:
            raise ServiceUnavailableException(detail="Client Redis non initialisé.")

        # Vérifier la connexion à la base de données de la KB
        if "postgresql" in settings.KB_DATABASE_URL:
            # Si le service de persistance gère la DB, on ping son health endpoint
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{settings.PERSISTENCE_SERVICE_URL}/health")
                resp.raise_for_status()
        elif "neo4j" in settings.KB_DATABASE_URL:
            # if app.state.neo4j_driver:
            #     await app.state.neo4j_driver.verify_connectivity()
            # else:
            #     raise ServiceUnavailableException(detail="Driver Neo4j non initialisé.")
            pass # Placeholder pour la vérification Neo4j

        return {"status": "ok", "message": "KB Service is healthy and connected to dependencies"}
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Dépendance non saine: {e}")

# Endpoint de préparation pour Kubernetes (readiness probe)
@app.get("/ready", status_code=status.HTTP_200_OK, summary="Vérifier la préparation du KB Service")
async def readiness_check():
    """
    Vérifie si le KB Service est prêt à recevoir du trafic.
    Doit inclure une vérification plus stricte de la disponibilité des dépendances.
    """
    settings = get_settings()
    try:
        # Vérifier la connexion Redis
        if redis_client:
            await redis_client.ping()
        else:
            raise ServiceUnavailableException(detail="Client Redis non initialisé.")

        # Vérifier la connexion à la base de données de la KB
        if "postgresql" in settings.KB_DATABASE_URL:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{settings.PERSISTENCE_SERVICE_URL}/ready")
                resp.raise_for_status()
        elif "neo4j" in settings.KB_DATABASE_URL:
            # if app.state.neo4j_driver:
            #     await app.state.neo4j_driver.verify_connectivity()
            # else:
            #     raise ServiceUnavailableException(detail="Driver Neo4j non initialisé.")
            pass # Placeholder pour la vérification Neo4j

        return {"status": "ready", "message": "KB Service is ready to serve requests"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Dépendance non prête: {e}")

