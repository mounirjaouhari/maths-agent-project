# backend/workflow-service/workflow/exceptions.py

from shared.exceptions import BadRequestException, InternalServerError, NotFoundException

class WorkflowException(InternalServerError):
    """Exception de base pour les erreurs spécifiques au service de workflow."""
    def __init__(self, detail: str = "Erreur du service de workflow"):
        super().__init__(detail=detail)

class InvalidTransitionError(BadRequestException):
    """Exception levée lorsqu'une transition d'état invalide est tentée."""
    def __init__(self, current_state: str, event: str, detail: str = "Transition d'état invalide"):
        super().__init__(detail=f"{detail}: L'événement '{event}' n'est pas permis depuis l'état '{current_state}'.")

class WorkflowPlanError(WorkflowException):
    """Exception levée en cas de problème avec le plan d'exécution du workflow (mode autonome)."""
    def __init__(self, detail: str = "Erreur de planification du workflow"):
        super().__init__(detail=detail)

class ProjectWorkflowNotFound(NotFoundException):
    """Exception levée lorsque le workflow d'un projet spécifique n'est pas trouvé ou n'est pas initialisé."""
    def __init__(self, project_id: str, detail: str = "Workflow de projet non trouvé"):
        super().__init__(detail=f"{detail} pour le projet {project_id}.")

class WorkflowInitializationError(WorkflowException):
    """Exception levée si le workflow ne peut pas être initialisé correctement."""
    def __init__(self, detail: str = "Échec de l'initialisation du workflow"):
        super().__init__(detail=detail)

