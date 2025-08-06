# Fichier placeholder pour middleware.py
# backend/api-gateway/core/middleware.py

from fastapi import FastAPI, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import uuid
import logging

from shared.exceptions import (
    UnauthorizedException, ForbiddenException, NotFoundException,
    BadRequestException, ConflictException, ServiceUnavailableException,
    InternalServerError
)

logger = logging.getLogger(__name__)

class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour ajouter un ID de corrélation (request_id) à chaque requête
    et le propager dans les logs et les en-têtes de réponse.
    """
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.app = app

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id # Stocke l'ID dans l'état de la requête

        # Ajoute l'ID de corrélation aux logs pour cette requête
        with logging.Logger.manager.disabled(): # Temporairement désactiver le gestionnaire pour éviter les conflits
            old_factory = logging.getLogRecordFactory()
            def record_factory(*args, **kwargs):
                record = old_factory(*args, **kwargs)
                record.request_id = request_id # Ajoute l'ID au LogRecord
                return record
            logging.setLogRecordFactory(record_factory)
            
            # Log de l'entrée de la requête
            logger.info(f"[{request_id}] Incoming request: {request.method} {request.url.path}")

            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time

            # Ajoute l'ID de corrélation à l'en-tête de la réponse
            response.headers["X-Request-ID"] = request_id

            # Log de la sortie de la requête
            logger.info(f"[{request_id}] Outgoing response: {response.status_code} in {process_time:.4f}s")
            
            # Réinitialise la factory de LogRecord
            logging.setLogRecordFactory(old_factory)
            
        return response

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour gérer les exceptions HTTP personnalisées et les erreurs inattendues,
    en assurant une réponse standardisée.
    """
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.app = app

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except UnauthorizedException as exc:
            logger.warning(f"[{getattr(request.state, 'request_id', 'N/A')}] Unauthorized: {exc.detail}")
            return Response(
                content=exc.detail,
                status_code=exc.status_code,
                headers={"WWW-Authenticate": "Bearer"}
            )
        except ForbiddenException as exc:
            logger.warning(f"[{getattr(request.state, 'request_id', 'N/A')}] Forbidden: {exc.detail}")
            return Response(
                content=exc.detail,
                status_code=exc.status_code
            )
        except NotFoundException as exc:
            logger.info(f"[{getattr(request.state, 'request_id', 'N/A')}] Not Found: {exc.detail}")
            return Response(
                content=exc.detail,
                status_code=exc.status_code
            )
        except BadRequestException as exc:
            logger.warning(f"[{getattr(request.state, 'request_id', 'N/A')}] Bad Request: {exc.detail}")
            return Response(
                content=exc.detail,
                status_code=exc.status_code
            )
        except ConflictException as exc:
            logger.warning(f"[{getattr(request.state, 'request_id', 'N/A')}] Conflict: {exc.detail}")
            return Response(
                content=exc.detail,
                status_code=exc.status_code
            )
        except ServiceUnavailableException as exc:
            logger.error(f"[{getattr(request.state, 'request_id', 'N/A')}] Service Unavailable: {exc.detail}", exc_info=True)
            return Response(
                content=exc.detail,
                status_code=exc.status_code
            )
        except Exception as exc:
            # Gérer toute autre exception non capturée
            logger.critical(f"[{getattr(request.state, 'request_id', 'N/A')}] Unhandled exception: {exc}", exc_info=True)
            return Response(
                content="Une erreur interne du serveur est survenue.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

def setup_middlewares(app: FastAPI):
    """
    Configure et ajoute les middlewares à l'application FastAPI.
    """
    # L'ordre des middlewares est important:
    # Les middlewares ajoutés en dernier sont exécutés en premier sur la requête entrante
    # et en dernier sur la réponse sortante.
    
    # Le middleware de gestion d'erreurs doit être le plus externe pour capturer toutes les exceptions
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Le middleware de contexte de requête (pour request_id) doit être avant les autres logiques
    app.add_middleware(RequestContextMiddleware)
    
    # D'autres middlewares pourraient être ajoutés ici (ex: compression, rate limiting)
