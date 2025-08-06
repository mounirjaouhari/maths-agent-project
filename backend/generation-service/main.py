# backend/generation-service/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from contextlib import asynccontextmanager
import logging
import httpx

from shared.config import get_settings
from shared.exceptions import (
    NotFoundException, BadRequestException, ServiceUnavailableException,
    InternalServerError, LLMAPIError, PromptBuildingError
)
from .api.internal import endpoints as internal_endpoints # Importe les routeurs d'endpoints internes
from .generation.llm_wrappers import LLMWrapper # Importe le wrapper LLM pour l'initialisation
from .generation.prompt_builder import PromptBuilder # Importe le prompt builder
from .generation.llm_selector import LLMSelector # Importe le LLM selector

# Configure le logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables globales pour les clients/instances
llm_wrapper: Optional[LLMWrapper] = None
prompt_builder: Optional[PromptBuilder] = None
llm_selector: Optional[LLMSelector] = None

# Gestionnaire de contexte asynchrone pour les événements de démarrage et d'arrêt de l'application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Fonctions exécutées au démarrage et à l'arrêt de l'application FastAPI.
    Initialise les clients LLM et les modules de génération.
    """
    settings = get_settings()
    logger.info(f"Démarrage du Generation Service en mode {settings.ENVIRONMENT}...")
    
    global llm_wrapper, prompt_builder, llm_selector
    
    # Initialiser le LLMWrapper avec les clés API
    llm_wrapper = LLMWrapper(
        openai_api_key=settings.OPENAI_API_KEY,
        google_ai_api_key=settings.GOOGLE_AI_API_KEY,
        anthropic_api_key=settings.ANTHROPIC_API_KEY
    )

    # Initialiser le PromptBuilder et le LLMSelector
    # Ces modules nécessitent l'accès au KB Service
    try:
        # Vérifier la connexion au KB Service au démarrage
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.KB_SERVICE_URL}/health")
            resp.raise_for_status()
        logger.info("Connexion au KB Service établie avec succès.")

        prompt_builder = PromptBuilder(kb_service_url=settings.KB_SERVICE_URL)
        llm_selector = LLMSelector(kb_service_url=settings.KB_SERVICE_URL)
        
    except httpx.HTTPStatusError as e:
        logger.error(f"KB Service non sain au démarrage: {e.response.text}")
        raise RuntimeError("KB Service non disponible, le Generation Service ne peut pas démarrer.")
    except httpx.RequestError as e:
        logger.error(f"Erreur réseau vers KB Service au démarrage: {e}")
        raise RuntimeError("Impossible de se connecter au KB Service, le Generation Service ne peut pas démarrer.")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du PromptBuilder/LLMSelector: {e}", exc_info=True)
        raise RuntimeError("Échec de l'initialisation des modules de génération.")

    yield # L'application est maintenant prête à servir les requêtes

    logger.info("Arrêt du Generation Service...")
    # Ici, vous pouvez ajouter des logiques d'arrêt, par exemple:
    # - Fermer des sessions HTTP (si non gérées par httpx.AsyncClient dans les appels)

# Initialisation de l'application FastAPI
app = FastAPI(
    title=get_settings().APP_NAME + " - Generation Service",
    description="Service interne pour la génération et le raffinement de contenu mathématique.",
    version="1.0.0",
    docs_url="/docs", # URL pour la documentation OpenAPI (Swagger UI)
    redoc_url="/redoc", # URL pour la documentation ReDoc
    lifespan=lifespan # Associe le gestionnaire de contexte
)

# Inclusion des routeurs API internes
app.include_router(internal_endpoints.router, prefix="/internal", tags=["internal"])

# Endpoint de santé de base pour Kubernetes (liveness probe)
@app.get("/health", status_code=status.HTTP_200_OK, summary="Vérifier la santé du Generation Service")
async def health_check():
    """
    Vérifie si le Generation Service est en cours d'exécution et peut se connecter à ses dépendances critiques.
    """
    settings = get_settings()
    try:
        # Vérifier que les modules sont initialisés
        if not llm_wrapper or not prompt_builder or not llm_selector:
            raise ServiceUnavailableException(detail="Modules de génération non initialisés.")

        # Vérifier la connexion au KB Service
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.KB_SERVICE_URL}/health")
            resp.raise_for_status()
        
        # Optionnel: Tenter un appel simple à un LLM pour vérifier la connectivité
        # try:
        #     await llm_wrapper.call_llm("gpt-3.5-turbo", "ping", {})
        # except Exception as e:
        #     logger.warning(f"LLM connectivity check failed: {e}")
        #     raise ServiceUnavailableException(detail="Connectivité LLM non fonctionnelle.")

        return {"status": "ok", "message": "Generation Service is healthy and connected to dependencies"}
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Dépendance non saine: {e}")

# Endpoint de préparation pour Kubernetes (readiness probe)
@app.get("/ready", status_code=status.HTTP_200_OK, summary="Vérifier la préparation du Generation Service")
async def readiness_check():
    """
    Vérifie si le Generation Service est prêt à recevoir du trafic.
    Doit inclure une vérification plus stricte de la disponibilité des dépendances.
    """
    settings = get_settings()
    try:
        if not llm_wrapper or not prompt_builder or not llm_selector:
            raise ServiceUnavailableException(detail="Modules de génération non initialisés.")

        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.KB_SERVICE_URL}/ready")
            resp.raise_for_status()

        # Optionnel: Tenter un appel plus approfondi à un LLM pour vérifier la préparation
        # try:
        #     await llm_wrapper.call_llm("gpt-3.5-turbo", "test prompt", {})
        # except Exception as e:
        #     logger.warning(f"LLM readiness check failed: {e}")
        #     raise ServiceUnavailableException(detail="LLM non prêt à générer.")

        return {"status": "ready", "message": "Generation Service is ready to serve requests"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Dépendance non prête: {e}")

