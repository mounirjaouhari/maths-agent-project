# Fichier placeholder pour main.py
# backend/interaction-service/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from contextlib import asynccontextmanager
import logging
import httpx

from shared.config import get_settings
from shared.exceptions import (
    NotFoundException, BadRequestException, ServiceUnavailableException,
    InternalServerError, LLMGenerationError
)
from .api.internal import endpoints as internal_endpoints # Importe les routeurs d'endpoints internes
from .refinement.feedback_analyzer import FeedbackAnalyzer # Importe l'analyseur de feedback
from .refinement.refinement_engine import RefinementEngine # Importe le moteur de raffinement

# Configure le logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables globales pour les clients/instances des sous-modules
feedback_analyzer: Optional[FeedbackAnalyzer] = None
refinement_engine: Optional[RefinementEngine] = None

# Gestionnaire de contexte asynchrone pour les événements de démarrage et d'arrêt de l'application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Fonctions exécutées au démarrage et à l'arrêt de l'application FastAPI.
    Initialise les sous-modules d'interaction et de raffinement.
    """
    settings = get_settings()
    logger.info(f"Démarrage du Interaction Service en mode {settings.ENVIRONMENT}...")
    
    global feedback_analyzer, refinement_engine
    
    try:
        # Vérifier la connexion aux services dépendants au démarrage
        async with httpx.AsyncClient() as client:
            resp_gen = await client.get(f"{settings.GENERATION_SERVICE_URL}/health")
            resp_gen.raise_for_status()
            resp_kb = await client.get(f"{settings.KB_SERVICE_URL}/health")
            resp_kb.raise_for_status()
        logger.info("Connexion aux services Generation et KB établie avec succès.")

        # Initialiser les sous-modules
        feedback_analyzer = FeedbackAnalyzer() # L'analyseur de feedback n'a pas de dépendances directes ici
        refinement_engine = RefinementEngine(
            generation_service_url=settings.GENERATION_SERVICE_URL,
            kb_service_url=settings.KB_SERVICE_URL
        )
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Service dépendant non sain au démarrage: {e.request.url} - {e.response.text}")
        raise RuntimeError(f"Service dépendant non disponible, le Interaction Service ne peut pas démarrer: {e.request.url}")
    except httpx.RequestError as e:
        logger.error(f"Erreur réseau vers service dépendant au démarrage: {e.request.url} - {e}")
        raise RuntimeError(f"Impossible de se connecter à un service dépendant, le Interaction Service ne peut pas démarrer: {e.request.url}")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation des sous-modules d'interaction: {e}", exc_info=True)
        raise RuntimeError("Échec de l'initialisation des modules d'interaction.")

    yield # L'application est maintenant prête à servir les requêtes

    logger.info("Arrêt du Interaction Service...")
    # Ici, vous pouvez ajouter des logiques d'arrêt

# Initialisation de l'application FastAPI
app = FastAPI(
    title=get_settings().APP_NAME + " - Interaction Service",
    description="Service interne pour l'analyse du feedback et le raffinement de contenu.",
    version="1.0.0",
    docs_url="/docs", # URL pour la documentation OpenAPI (Swagger UI)
    redoc_url="/redoc", # URL pour la documentation ReDoc
    lifespan=lifespan # Associe le gestionnaire de contexte
)

# Inclusion des routeurs API internes
app.include_router(internal_endpoints.router, prefix="/internal", tags=["internal"])

# Endpoint de santé de base pour Kubernetes (liveness probe)
@app.get("/health", status_code=status.HTTP_200_OK, summary="Vérifier la santé du Interaction Service")
async def health_check():
    """
    Vérifie si le Interaction Service est en cours d'exécution et peut se connecter à ses dépendances critiques.
    """
    settings = get_settings()
    try:
        # Vérifier que les modules sont initialisés
        if not feedback_analyzer or not refinement_engine:
            raise ServiceUnavailableException(detail="Modules d'interaction non initialisés.")

        # Vérifier la connexion aux services dépendants
        async with httpx.AsyncClient() as client:
            resp_gen = await client.get(f"{settings.GENERATION_SERVICE_URL}/health")
            resp_gen.raise_for_status()
            resp_kb = await client.get(f"{settings.KB_SERVICE_URL}/health")
            resp_kb.raise_for_status()

        return {"status": "ok", "message": "Interaction Service is healthy and connected to dependencies"}
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Dépendance non saine: {e}")

# Endpoint de préparation pour Kubernetes (readiness probe)
@app.get("/ready", status_code=status.HTTP_200_OK, summary="Vérifier la préparation du Interaction Service")
async def readiness_check():
    """
    Vérifie si le Interaction Service est prêt à recevoir du trafic.
    Doit inclure une vérification plus stricte de la disponibilité des dépendances.
    """
    settings = get_settings()
    try:
        if not feedback_analyzer or not refinement_engine:
            raise ServiceUnavailableException(detail="Modules d'interaction non initialisés.")

        async with httpx.AsyncClient() as client:
            resp_gen = await client.get(f"{settings.GENERATION_SERVICE_URL}/ready")
            resp_gen.raise_for_status()
            resp_kb = await client.get(f"{settings.KB_SERVICE_URL}/ready")
            resp_kb.raise_for_status()

        return {"status": "ready", "message": "Interaction Service is ready to serve requests"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Dépendance non prête: {e}")

