# backend/workflow-service/workflow/state_manager.py

import logging
from uuid import UUID
import httpx
from typing import Dict, Any, Optional

from shared.config import get_settings
from shared.models import ProjectResponse, ContentBlockResponse, DocumentVersionResponse
from shared.exceptions import NotFoundException, ServiceUnavailableException, BadRequestException
from .state_machine import ContentBlockStateMachine # Importe la FSM

logger = logging.getLogger(__name__)
settings = get_settings()

class WorkflowStateManager:
    """
    Gère le chargement et la sauvegarde de l'état des entités du workflow
    (projets, blocs de contenu) depuis et vers le service de persistance.
    """
    def __init__(self, persistence_service_url: str):
        self.persistence_service_url = persistence_service_url

    async def get_project_state(self, project_id: UUID) -> ProjectResponse:
        """
        Récupère l'état complet d'un projet depuis le service de persistance.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.persistence_service_url}/internal/projects/{project_id}")
                response.raise_for_status()
                return ProjectResponse(**response.json())
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise NotFoundException(detail=f"Projet avec l'ID {project_id} non trouvé.")
                logger.error(f"Erreur HTTP lors de la récupération de l'état du projet {project_id}: {e.response.text}")
                raise ServiceUnavailableException(detail="Erreur du service de persistance.")
            except httpx.RequestError as e:
                logger.error(f"Erreur réseau lors de la récupération de l'état du projet {project_id}: {e}")
                raise ServiceUnavailableException(detail="Le service de persistance n'est pas disponible.")

    async def update_project_state(self, project_id: UUID, status: str, current_step: Optional[str] = None) -> ProjectResponse:
        """
        Met à jour le statut et l'étape d'un projet dans le service de persistance.
        """
        async with httpx.AsyncClient() as client:
            try:
                update_data = {"status": status}
                if current_step:
                    update_data["current_step"] = current_step
                response = await client.put(f"{self.persistence_service_url}/internal/projects/{project_id}", json=update_data)
                response.raise_for_status()
                logger.info(f"Projet {project_id} mis à jour au statut '{status}' (étape: {current_step})")
                return ProjectResponse(**response.json())
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise NotFoundException(detail=f"Projet avec l'ID {project_id} non trouvé pour mise à jour.")
                logger.error(f"Erreur HTTP lors de la mise à jour de l'état du projet {project_id}: {e.response.text}")
                raise ServiceUnavailableException(detail="Erreur du service de persistance.")
            except httpx.RequestError as e:
                logger.error(f"Erreur réseau lors de la mise à jour de l'état du projet {project_id}: {e}")
                raise ServiceUnavailableException(detail="Le service de persistance n'est pas disponible.")

    async def get_content_block_state(self, block_id: UUID) -> ContentBlockResponse:
        """
        Récupère l'état complet d'un bloc de contenu depuis le service de persistance.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.persistence_service_url}/internal/content-blocks/{block_id}")
                response.raise_for_status()
                return ContentBlockResponse(**response.json())
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise NotFoundException(detail=f"Bloc de contenu avec l'ID {block_id} non trouvé.")
                logger.error(f"Erreur HTTP lors de la récupération de l'état du bloc {block_id}: {e.response.text}")
                raise ServiceUnavailableException(detail="Erreur du service de persistance.")
            except httpx.RequestError as e:
                logger.error(f"Erreur réseau lors de la récupération de l'état du bloc {block_id}: {e}")
                raise ServiceUnavailableException(detail="Le service de persistance n'est pas disponible.")

    async def update_content_block_state(self, block_id: UUID, update_data: Dict[str, Any]) -> ContentBlockResponse:
        """
        Met à jour l'état d'un bloc de contenu dans le service de persistance.
        update_data peut inclure 'status', 'content_latex', 'qc_report', etc.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(f"{self.persistence_service_url}/internal/content-blocks/{block_id}", json=update_data)
                response.raise_for_status()
                logger.info(f"Bloc {block_id} mis à jour avec les données: {update_data.keys()}")
                return ContentBlockResponse(**response.json())
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise NotFoundException(detail=f"Bloc de contenu avec l'ID {block_id} non trouvé pour mise à jour.")
                logger.error(f"Erreur HTTP lors de la mise à jour de l'état du bloc {block_id}: {e.response.text}")
                raise ServiceUnavailableException(detail="Erreur du service de persistance.")
            except httpx.RequestError as e:
                logger.error(f"Erreur réseau lors de la mise à jour de l'état du bloc {block_id}: {e}")
                raise ServiceUnavailableException(detail="Le service de persistance n'est pas disponible.")
            except Exception as e:
                logger.error(f"Erreur inattendue lors de la mise à jour du bloc {block_id}: {e}", exc_info=True)
                raise BadRequestException(detail=f"Échec de la mise à jour du bloc: {e}")

    async def create_content_block(self, block_data: Dict[str, Any]) -> ContentBlockResponse:
        """
        Crée un nouveau bloc de contenu dans le service de persistance.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.persistence_service_url}/internal/content-blocks", json=block_data)
                response.raise_for_status()
                logger.info(f"Nouveau bloc de contenu créé: {response.json().get('block_id')}")
                return ContentBlockResponse(**response.json())
            except httpx.HTTPStatusError as e:
                logger.error(f"Erreur HTTP lors de la création du bloc de contenu: {e.response.text}")
                raise BadRequestException(detail=f"Échec de la création du bloc: {e.response.text}")
            except httpx.RequestError as e:
                logger.error(f"Erreur réseau lors de la création du bloc de contenu: {e}")
                raise ServiceUnavailableException(detail="Le service de persistance n'est pas disponible.")

    async def get_document_version_state(self, version_id: UUID) -> DocumentVersionResponse:
        """
        Récupère l'état d'une version de document.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.persistence_service_url}/internal/document-versions/{version_id}")
                response.raise_for_status()
                return DocumentVersionResponse(**response.json())
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise NotFoundException(detail=f"Version de document avec l'ID {version_id} non trouvée.")
                logger.error(f"Erreur HTTP lors de la récupération de la version du document {version_id}: {e.response.text}")
                raise ServiceUnavailableException(detail="Erreur du service de persistance.")
            except httpx.RequestError as e:
                logger.error(f"Erreur réseau lors de la récupération de la version du document {version_id}: {e}")
                raise ServiceUnavailableException(detail="Le service de persistance n'est pas disponible.")
    
    async def get_all_content_blocks_for_version(self, version_id: UUID) -> List[ContentBlockResponse]:
        """
        Récupère tous les blocs de contenu pour une version de document donnée.
        """
        async with httpx.AsyncClient() as client:
            try:
                # Cet endpoint doit être implémenté dans le service de persistance
                response = await client.get(f"{self.persistence_service_url}/internal/content-blocks/version/{version_id}")
                response.raise_for_status()
                return [ContentBlockResponse(**cb) for cb in response.json()]
            except httpx.HTTPStatusError as e:
                logger.error(f"Erreur HTTP lors de la récupération des blocs pour la version {version_id}: {e.response.text}")
                raise ServiceUnavailableException(detail="Erreur du service de persistance lors de la récupération des blocs.")
            except httpx.RequestError as e:
                logger.error(f"Erreur réseau lors de la récupération des blocs pour la version {version_id}: {e}")
                raise ServiceUnavailableException(detail="Le service de persistance n'est pas disponible.")


# Instancier le gestionnaire d'état
workflow_state_manager = WorkflowStateManager(
    persistence_service_url=settings.PERSISTENCE_SERVICE_URL
)
