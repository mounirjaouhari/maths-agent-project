# Fichier placeholder pour exceptions.py
# backend/shared/exceptions.py

from fastapi import HTTPException, status

# --- Exceptions Générales de l'Application ---

class NotFoundException(HTTPException):
    """Exception levée lorsqu'une ressource demandée n'est pas trouvée."""
    def __init__(self, detail: str = "Ressource non trouvée"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class BadRequestException(HTTPException):
    """Exception levée lorsque la requête est mal formée ou contient des données invalides."""
    def __init__(self, detail: str = "Requête invalide"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class UnauthorizedException(HTTPException):
    """Exception levée lorsque l'authentification échoue ou est manquante."""
    def __init__(self, detail: str = "Non authentifié"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail,
                         headers={"WWW-Authenticate": "Bearer"})

class ForbiddenException(HTTPException):
    """Exception levée lorsque l'utilisateur n'a pas les permissions nécessaires pour accéder à la ressource."""
    def __init__(self, detail: str = "Accès non autorisé"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

class ConflictException(HTTPException):
    """Exception levée lorsqu'il y a un conflit avec l'état actuel de la ressource (ex: ressource déjà existante)."""
    def __init__(self, detail: str = "Conflit de ressource"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

class ServiceUnavailableException(HTTPException):
    """Exception levée lorsqu'un service dépendant est temporairement indisponible."""
    def __init__(self, detail: str = "Service externe temporairement indisponible"):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

class InternalServerError(HTTPException):
    """Exception générique pour les erreurs internes du serveur."""
    def __init__(self, detail: str = "Erreur interne du serveur"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


# --- Exceptions Spécifiques au Domaine ---

class ProjectNotFoundException(NotFoundException):
    """Exception spécifique lorsqu'un projet n'est pas trouvé."""
    def __init__(self, project_id: str):
        super().__init__(detail=f"Projet avec l'ID {project_id} non trouvé")

class UserNotFoundException(NotFoundException):
    """Exception spécifique lorsqu'un utilisateur n'est pas trouvé."""
    def __init__(self, user_id: str):
        super().__init__(detail=f"Utilisateur avec l'ID {user_id} non trouvé")

class ContentBlockNotFoundException(NotFoundException):
    """Exception spécifique lorsqu'un bloc de contenu n'est pas trouvé."""
    def __init__(self, block_id: str):
        super().__init__(detail=f"Bloc de contenu avec l'ID {block_id} non trouvé")

class DocumentVersionNotFoundException(NotFoundException):
    """Exception spécifique lorsqu'une version de document n'est pas trouvée."""
    def __init__(self, version_id: str):
        super().__init__(detail=f"Version de document avec l'ID {version_id} non trouvée")

class InvalidWorkflowStateException(BadRequestException):
    """Exception levée lorsqu'une opération de workflow est tentée dans un état invalide."""
    def __init__(self, current_status: str, attempted_action: str):
        super().__init__(detail=f"Action '{attempted_action}' non permise dans l'état actuel du workflow: '{current_status}'")

class LLMGenerationError(InternalServerError):
    """Exception levée lorsqu'une erreur survient lors de la génération de contenu par un LLM."""
    def __init__(self, detail: str = "Échec de la génération de contenu par le LLM"):
        super().__init__(detail=detail)

class QCAnalysisError(InternalServerError):
    """Exception levée lorsqu'une erreur survient lors de l'analyse QC."""
    def __init__(self, detail: str = "Échec de l'analyse de contrôle qualité"):
        super().__init__(detail=detail)

class ExternalToolError(InternalServerError):
    """Exception levée lorsqu'une erreur survient lors de l'interaction avec un outil externe (ex: solveur mathématique, Pandoc)."""
    def __init__(self, tool_name: str, detail: str = "Erreur lors de l'appel à l'outil externe"):
        super().__init__(detail=f"{detail}: {tool_name}")

class PromptBuildingError(BadRequestException):
    """Exception levée si le prompt ne peut pas être construit correctement."""
    def __init__(self, detail: str = "Échec de la construction du prompt"):
        super().__init__(detail=detail)

class LLMAPIError(ServiceUnavailableException):
    """Exception levée pour les erreurs spécifiques aux APIs LLM (ex: rate limit, service indisponible)."""
    def __init__(self, llm_name: str, original_detail: str = "Erreur de l'API LLM"):
        super().__init__(detail=f"{original_detail} pour {llm_name}")

class DocumentAssemblyError(InternalServerError):
    """Exception levée en cas d'échec de l'assemblage du document."""
    def __init__(self, detail: str = "Échec de l'assemblage du document"):
        super().__init__(detail=detail)

class DocumentExportError(InternalServerError):
    """Exception levée en cas d'échec de l'exportation du document."""
    def __init__(self, detail: str = "Échec de l'exportation du document"):
        super().__init__(detail=detail)

