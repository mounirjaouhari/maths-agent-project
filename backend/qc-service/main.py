# backend/qc-service/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from contextlib import asynccontextmanager
import logging
import httpx

from shared.config import get_settings
from shared.exceptions import (
    NotFoundException, BadRequestException, ServiceUnavailableException,
    InternalServerError, QCAnalysisError, ExternalToolError
)
from .api.internal import endpoints as internal_endpoints # Importe les routeurs d'endpoints internes
from .qc.math_verifier import MathVerifier # Importe le vérificateur mathématique
from .qc.pedagogic_analyzer import PedagogicAnalyzer # Importe l'analyseur pédagogique
from .qc.coherence_analyzer import CoherenceAnalyzer # Importe l'analyseur de cohérence
from .qc.score_calculator import ScoreCalculator # Importe le calculateur de score

# Configure le logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables globales pour les clients/instances des sous-modules QC
math_verifier: Optional[MathVerifier] = None
pedagogic_analyzer: Optional[PedagogicAnalyzer] = None
coherence_analyzer: Optional[CoherenceAnalyzer] = None
score_calculator: Optional[ScoreCalculator] = None

# Gestionnaire de contexte asynchrone pour les événements de démarrage et d'arrêt de l'application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Fonctions exécutées au démarrage et à l'arrêt de l'application FastAPI.
    Initialise les sous-modules QC et leurs dépendances.
    """
    settings = get_settings()
    logger.info(f"Démarrage du QC Service en mode {settings.ENVIRONMENT}...")
    
    global math_verifier, pedagogic_analyzer, coherence_analyzer, score_calculator
    
    try:
        # Vérifier la connexion au KB Service au démarrage
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.KB_SERVICE_URL}/health")
            resp.raise_for_status()
        logger.info("Connexion au KB Service établie avec succès.")

        # Initialiser les sous-modules QC
        math_verifier = MathVerifier(kb_service_url=settings.KB_SERVICE_URL, external_tools_path=settings.QC_MATH_VERIFIER_TOOLS_PATH)
        pedagogic_analyzer = PedagogicAnalyzer(kb_service_url=settings.KB_SERVICE_URL)
        coherence_analyzer = CoherenceAnalyzer(kb_service_url=settings.KB_SERVICE_URL, persistence_service_url=settings.PERSISTENCE_SERVICE_URL)
        score_calculator = ScoreCalculator()
        
    except httpx.HTTPStatusError as e:
        logger.error(f"KB Service non sain au démarrage: {e.response.text}")
        raise RuntimeError("KB Service non disponible, le QC Service ne peut pas démarrer.")
    except httpx.RequestError as e:
        logger.error(f"Erreur réseau vers KB Service au démarrage: {e}")
        raise RuntimeError("Impossible de se connecter au KB Service, le QC Service ne peut pas démarrer.")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation des sous-modules QC: {e}", exc_info=True)
        raise RuntimeError("Échec de l'initialisation des modules QC.")

    yield # L'application est maintenant prête à servir les requêtes

    logger.info("Arrêt du QC Service...")
    # Ici, vous pouvez ajouter des logiques d'arrêt, par exemple:
    # - Fermer des sessions HTTP
    # - Nettoyer des ressources liées aux outils externes
    # math_verifier.cleanup() # Si le vérificateur a des ressources à nettoyer

# Initialisation de l'application FastAPI
app = FastAPI(
    title=get_settings().APP_NAME + " - QC Service",
    description="Service interne pour le contrôle qualité et la vérification du contenu mathématique.",
    version="1.0.0",
    docs_url="/docs", # URL pour la documentation OpenAPI (Swagger UI)
    redoc_url="/redoc", # URL pour la documentation ReDoc
    lifespan=lifespan # Associe le gestionnaire de contexte
)

# Inclusion des routeurs API internes
app.include_router(internal_endpoints.router, prefix="/internal", tags=["internal"])

# Endpoint de santé de base pour Kubernetes (liveness probe)
@app.get("/health", status_code=status.HTTP_200_OK, summary="Vérifier la santé du QC Service")
async def health_check():
    """
    Vérifie si le QC Service est en cours d'exécution et peut se connecter à ses dépendances critiques.
    """
    settings = get_settings()
    try:
        # Vérifier que les modules sont initialisés
        if not math_verifier or not pedagogic_analyzer or not coherence_analyzer or not score_calculator:
            raise ServiceUnavailableException(detail="Modules QC non initialisés.")

        # Vérifier la connexion au KB Service
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.KB_SERVICE_URL}/health")
            resp.raise_for_status()
        
        # Optionnel: Tenter un appel simple à un outil externe pour vérifier la connectivité
        # try:
        #     await math_verifier.check_tool_connectivity("sympy") # Exemple
        # except Exception as e:
        #     logger.warning(f"External tool connectivity check failed: {e}")
        #     raise ServiceUnavailableException(detail="Connectivité aux outils externes non fonctionnelle.")

        return {"status": "ok", "message": "QC Service is healthy and connected to dependencies"}
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Dépendance non saine: {e}")

# Endpoint de préparation pour Kubernetes (readiness probe)
@app.get("/ready", status_code=status.HTTP_200_OK, summary="Vérifier la préparation du QC Service")
async def readiness_check():
    """
    Vérifie si le QC Service est prêt à recevoir du trafic.
    Doit inclure une vérification plus stricte de la disponibilité des dépendances.
    """
    settings = get_settings()
    try:
        if not math_verifier or not pedagogic_analyzer or not coherence_analyzer or not score_calculator:
            raise ServiceUnavailableException(detail="Modules QC non initialisés.")

        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.KB_SERVICE_URL}/ready")
            resp.raise_for_status()

        # Optionnel: Tenter un appel plus approfondi aux outils externes pour vérifier la préparation
        # try:
        #     await math_verifier.verify_mathematical_statement("1+1=2")
        # except Exception as e:
        #     logger.warning(f"External tool readiness check failed: {e}")
        #     raise ServiceUnavailableException(detail="Outils externes non prêts pour l'analyse.")

        return {"status": "ready", "message": "QC Service is ready to serve requests"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Dépendance non prête: {e}")

