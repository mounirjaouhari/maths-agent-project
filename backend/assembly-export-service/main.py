# Fichier placeholder pour main.py
# backend/assembly-export-service/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from contextlib import asynccontextmanager
import logging
import httpx

from shared.config import get_settings
from shared.exceptions import (
    NotFoundException, BadRequestException, ServiceUnavailableException,
    InternalServerError, DocumentAssemblyError, DocumentExportError, ExternalToolError
)
from .api.internal import endpoints as internal_endpoints # Importe les routeurs d'endpoints internes
from .assembly.assembler import DocumentAssembler # Importe l'assembleur de documents
from .export.exporter import DocumentExporter # Importe l'exportateur de documents

# Configure le logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables globales pour les clients/instances des sous-modules
document_assembler: Optional[DocumentAssembler] = None
document_exporter: Optional[DocumentExporter] = None

# Gestionnaire de contexte asynchrone pour les événements de démarrage et d'arrêt de l'application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Fonctions exécutées au démarrage et à l'arrêt de l'application FastAPI.
    Initialise les sous-modules d'assemblage et d'exportation.
    """
    settings = get_settings()
    logger.info(f"Démarrage du Assembly Export Service en mode {settings.ENVIRONMENT}...")
    
    global document_assembler, document_exporter
    
    try:
        # Vérifier la connexion au Persistence Service au démarrage
        async with httpx.AsyncClient() as client:
            resp_pers = await client.get(f"{settings.PERSISTENCE_SERVICE_URL}/health")
            resp_pers.raise_for_status()
        logger.info("Connexion au Persistence Service établie avec succès.")

        # Initialiser les sous-modules
        document_assembler = DocumentAssembler(persistence_service_url=settings.PERSISTENCE_SERVICE_URL)
        document_exporter = DocumentExporter(
            pandoc_path=settings.PANDOC_PATH,
            pdflatex_path=settings.PDFLATEX_PATH
        )
        
        # Optionnel: Vérifier la disponibilité des outils externes au démarrage
        # try:
        #     await document_exporter.check_tool_availability()
        # except ExternalToolError as e:
        #     logger.error(f"Outils d'exportation externes non disponibles: {e.detail}")
        #     raise RuntimeError(f"Outils d'exportation externes non disponibles: {e.detail}")

    except httpx.HTTPStatusError as e:
        logger.error(f"Persistence Service non sain au démarrage: {e.request.url} - {e.response.text}")
        raise RuntimeError(f"Persistence Service non disponible, le Assembly Export Service ne peut pas démarrer: {e.request.url}")
    except httpx.RequestError as e:
        logger.error(f"Erreur réseau vers Persistence Service au démarrage: {e.request.url} - {e}")
        raise RuntimeError(f"Impossible de se connecter au Persistence Service, le Assembly Export Service ne peut pas démarrer: {e.request.url}")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation des sous-modules d'assemblage/exportation: {e}", exc_info=True)
        raise RuntimeError("Échec de l'initialisation des modules d'assemblage/exportation.")

    yield # L'application est maintenant prête à servir les requêtes

    logger.info("Arrêt du Assembly Export Service...")
    # Ici, vous pouvez ajouter des logiques d'arrêt

# Initialisation de l'application FastAPI
app = FastAPI(
    title=get_settings().APP_NAME + " - Assembly Export Service",
    description="Service interne pour l'assemblage et l'exportation des documents mathématiques.",
    version="1.0.0",
    docs_url="/docs", # URL pour la documentation OpenAPI (Swagger UI)
    redoc_url="/redoc", # URL pour la documentation ReDoc
    lifespan=lifespan # Associe le gestionnaire de contexte
)

# Inclusion des routeurs API internes
app.include_router(internal_endpoints.router, prefix="/internal", tags=["internal"])

# Endpoint de santé de base pour Kubernetes (liveness probe)
@app.get("/health", status_code=status.HTTP_200_OK, summary="Vérifier la santé du Assembly Export Service")
async def health_check():
    """
    Vérifie si le Assembly Export Service est en cours d'exécution et peut se connecter à ses dépendances critiques.
    """
    settings = get_settings()
    try:
        # Vérifier que les modules sont initialisés
        if not document_assembler or not document_exporter:
            raise ServiceUnavailableException(detail="Modules d'assemblage/exportation non initialisés.")

        # Vérifier la connexion au Persistence Service
        async with httpx.AsyncClient() as client:
            resp_pers = await client.get(f"{settings.PERSISTENCE_SERVICE_URL}/health")
            resp_pers.raise_for_status()
        
        # Optionnel: Vérifier la disponibilité des outils externes
        # await document_exporter.check_tool_availability()

        return {"status": "ok", "message": "Assembly Export Service is healthy and connected to dependencies"}
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Dépendance non saine: {e}")

# Endpoint de préparation pour Kubernetes (readiness probe)
@app.get("/ready", status_code=status.HTTP_200_OK, summary="Vérifier la préparation du Assembly Export Service")
async def readiness_check():
    """
    Vérifie si le Assembly Export Service est prêt à recevoir du trafic.
    Doit inclure une vérification plus stricte de la disponibilité des dépendances.
    """
    settings = get_settings()
    try:
        if not document_assembler or not document_exporter:
            raise ServiceUnavailableException(detail="Modules d'assemblage/exportation non initialisés.")

        async with httpx.AsyncClient() as client:
            resp_pers = await client.get(f"{settings.PERSISTENCE_SERVICE_URL}/ready")
            resp_pers.raise_for_status()

        # Optionnel: Tenter une petite opération avec les outils externes pour vérifier la préparation
        # await document_exporter.check_tool_availability() # Vérification plus approfondie

        return {"status": "ready", "message": "Assembly Export Service is ready to serve requests"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Dépendance non prête: {e}")

