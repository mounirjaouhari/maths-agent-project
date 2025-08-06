# backend/api-gateway/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from shared.config import get_settings
from shared.exceptions import UnauthorizedException, ForbiddenException, NotFoundException, BadRequestException
from .api.v1.endpoints import users, projects # Importe les routeurs d'endpoints
from .auth import security, dependencies
from .core.middleware import setup_middlewares # Pour les middlewares personnalisés

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
    logger.info(f"Démarrage de l'API Gateway en mode {settings.ENVIRONMENT}...")
    
    # Ici, vous pouvez ajouter des logiques de démarrage, par exemple:
    # - Initialiser des connexions à des bases de données si l'API Gateway en a besoin directement
    # - Charger des configurations ou des clés
    
    yield # L'application est maintenant prête à servir les requêtes

    logger.info("Arrêt de l'API Gateway...")
    # Ici, vous pouvez ajouter des logiques d'arrêt, par exemple:
    # - Fermer des connexions à des bases de données
    # - Nettoyer des ressources

# Initialisation de l'application FastAPI
app = FastAPI(
    title=get_settings().APP_NAME + " - API Gateway",
    description="API publique pour interagir avec l'Agent IA de Rédaction Mathématique.",
    version="1.0.0",
    docs_url="/docs", # URL pour la documentation OpenAPI (Swagger UI)
    redoc_url="/redoc", # URL pour la documentation ReDoc
    lifespan=lifespan # Associe le gestionnaire de contexte
)

# Configuration des CORS (Cross-Origin Resource Sharing)
# Permet aux applications frontend (sur des domaines différents) d'accéder à l'API
origins = [
    "http://localhost",
    "http://localhost:3000", # Exemple pour un frontend React ou Vue en développement
    get_settings().FRONTEND_URL # L'URL de votre frontend en production/staging (à définir dans config.py)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Autorise toutes les méthodes HTTP (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Autorise tous les en-têtes HTTP
)

# Configuration des middlewares personnalisés (logging, gestion des erreurs, etc.)
setup_middlewares(app)

# Inclusion des routeurs API
# Ces routeurs définissent les endpoints pour les différentes ressources (utilisateurs, projets)
app.include_router(users.router, prefix="/v1/users", tags=["users"])
app.include_router(projects.router, prefix="/v1/projects", tags=["projects"])

# Endpoint de santé de base pour Kubernetes (liveness probe)
@app.get("/health", status_code=status.HTTP_200_OK, summary="Vérifier la santé de l'API Gateway")
async def health_check():
    """
    Vérifie si l'API Gateway est en cours d'exécution.
    """
    return {"status": "ok", "message": "API Gateway is healthy"}

# Endpoint de préparation pour Kubernetes (readiness probe)
@app.get("/ready", status_code=status.HTTP_200_OK, summary="Vérifier la préparation de l'API Gateway")
async def readiness_check():
    """
    Vérifie si l'API Gateway est prête à recevoir du trafic.
    Peut inclure des vérifications de dépendances (DB, services internes) si nécessaire.
    """
    # Exemple: Vérifier si les services internes sont accessibles (simple ping ou connexion)
    # try:
    #     # await some_internal_service_client.ping()
    #     pass
    # except Exception as e:
    #     raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Dépendance non prête: {e}")
    return {"status": "ready", "message": "API Gateway is ready to serve requests"}

# Gestionnaire d'erreurs global (peut être déplacé dans middleware.py si plus complexe)
@app.exception_handler(UnauthorizedException)
async def unauthorized_exception_handler(request, exc: UnauthorizedException):
    logger.warning(f"Unauthorized access attempt: {exc.detail}")
    return HTTPException(status_code=exc.status_code, detail=exc.detail, headers=exc.headers)

@app.exception_handler(ForbiddenException)
async def forbidden_exception_handler(request, exc: ForbiddenException):
    logger.warning(f"Forbidden access attempt: {exc.detail}")
    return HTTPException(status_code=exc.status_code, detail=exc.detail)

@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request, exc: NotFoundException):
    logger.info(f"Resource not found: {exc.detail}")
    return HTTPException(status_code=exc.status_code, detail=exc.detail)

@app.exception_handler(BadRequestException)
async def bad_request_exception_handler(request, exc: BadRequestException):
    logger.warning(f"Bad request: {exc.detail}")
    return HTTPException(status_code=exc.status_code, detail=exc.detail)

# Pour démarrer l'application avec Uvicorn, utilisez la commande:
# uvicorn main:app --host 0.0.0.0 --port 8000
