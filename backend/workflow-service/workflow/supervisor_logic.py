# backend/workflow-service/workflow/supervisor_logic.py

import logging
from uuid import UUID
import httpx
from typing import Dict, Any

from shared.config import get_settings
from shared.exceptions import NotFoundException, BadRequestException, ServiceUnavailableException, InvalidWorkflowStateException
from shared.models import ProjectResponse, ContentBlockResponse, WorkflowSignal
from .state_machine import ContentBlockStateMachine, EVENTS
from ..tasks.workflow_tasks import (
    generate_content_block_task, 
    assemble_document_task, 
    export_document_task
) # Importe les tâches Celery

logger = logging.getLogger(__name__)
settings = get_settings()

class SupervisorLogic:
    """
    Implémente la logique spécifique au Mode Supervisé du Moteur de Workflow.
    Gère les interactions avec l'utilisateur et orchestre les tâches en conséquence.
    """
    def __init__(self, persistence_service_url: str):
        self.persistence_service_url = persistence_service_url

    async def _get_project_and_block(self, project_id: UUID, block_id: UUID = None) -> tuple[ProjectResponse, Optional[ContentBlockResponse]]:
        """Récupère le projet et un bloc de contenu si spécifié, depuis le service de persistance."""
        async with httpx.AsyncClient() as client:
            try:
                project_resp = await client.get(f"{self.persistence_service_url}/internal/projects/{project_id}")
                project_resp.raise_for_status()
                project = ProjectResponse(**project_resp.json())

                block = None
                if block_id:
                    block_resp = await client.get(f"{self.persistence_service_url}/internal/content-blocks/{block_id}")
                    block_resp.raise_for_status()
                    block = ContentBlockResponse(**block_resp.json())
                    # Vérifier que le bloc appartient bien à une version du document du projet
                    # (logique plus complexe si nécessaire, pour l'instant on suppose la cohérence)

                return project, block
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise NotFoundException(detail=f"Projet ou bloc non trouvé: {e.request.url}")
                logger.error(f"Erreur HTTP lors de la récupération du projet/bloc: {e.response.text}")
                raise ServiceUnavailableException(detail="Erreur du service de persistance.")
            except httpx.RequestError as e:
                logger.error(f"Erreur réseau lors de la récupération du projet/bloc: {e}")
                raise ServiceUnavailableException(detail="Le service de persistance n'est pas disponible.")

    async def _update_project_status(self, project_id: UUID, status: str, current_step: str = None):
        """Met à jour le statut du projet dans le service de persistance."""
        async with httpx.AsyncClient() as client:
            update_data = {"status": status}
            if current_step:
                update_data["current_step"] = current_step
            await client.put(f"{self.persistence_service_url}/internal/projects/{project_id}", json=update_data)
            logger.info(f"Projet {project_id} mis à jour au statut '{status}' (étape: {current_step})")

    async def _update_block_status(self, block_id: UUID, status: str, qc_report: Dict = None, refinement_attempts: int = None, error_message: str = None):
        """Met à jour le statut d'un bloc de contenu dans le service de persistance."""
        async with httpx.AsyncClient() as client:
            update_data = {"status": status}
            if qc_report:
                update_data["qc_report"] = qc_report
            if refinement_attempts is not None:
                update_data["refinement_attempts"] = refinement_attempts
            if error_message:
                update_data["error_message"] = error_message
            await client.put(f"{self.persistence_service_url}/internal/content-blocks/{block_id}", json=update_data)
            logger.info(f"Bloc {block_id} mis à jour au statut '{status}'")

    async def handle_user_signal(self, project_id: UUID, signal: WorkflowSignal) -> ProjectResponse:
        """
        Gère un signal utilisateur reçu par le moteur de workflow en mode Supervisé.
        """
        project, block = await self._get_project_and_block(project_id, signal.block_id)

        if project.mode != "Supervisé":
            raise BadRequestException(detail=f"Le projet {project_id} n'est pas en mode Supervisé.")

        # Initialiser la FSM du bloc si un block_id est fourni
        fsm = None
        if block:
            fsm = ContentBlockStateMachine(
                initial_state=block.status, 
                mode=project.mode, 
                block_id=block.block_id, 
                project_id=project.project_id
            )

        # Logique de gestion des signaux basée sur le type de signal
        if signal.signal_type == "VALIDATED":
            if not fsm:
                raise BadRequestException(detail="Un block_id est requis pour le signal VALIDATED.")
            
            # Tente la transition dans la FSM
            new_block_status = fsm.transition(EVENTS["USER_VALIDATE"])
            await self._update_block_status(block.block_id, new_block_status)
            
            # Ici, vous déclencheriez la prochaine étape du workflow (ex: générer le bloc suivant, passer à l'étape QC finale)
            # Cette logique serait plus détaillée et pourrait impliquer de vérifier l'état global du projet
            # et de déclencher de nouvelles tâches Celery.
            logger.info(f"Projet {project_id}: Bloc {block.block_id} validé par l'utilisateur. Prochaine étape à déterminer.")
            
            # Exemple: Si toutes les sections d'une étape sont validées, passer à la prochaine étape du protocole
            # (Cette logique globale est gérée par le Workflow Engine, pas seulement par le supervisor_logic)
            # Pour l'exemple, nous allons juste retourner le projet mis à jour
            return project # Retourne l'état actuel du projet

        elif signal.signal_type == "REDO":
            if not fsm or not signal.feedback:
                raise BadRequestException(detail="Un block_id et un feedback sont requis pour le signal REDO.")
            
            new_block_status = fsm.transition(EVENTS["USER_REDO"], user_feedback=signal.feedback)
            await self._update_block_status(block.block_id, new_block_status)
            
            # Déclencher la tâche de raffinement via Celery
            # Le service d'interaction/raffinement prendra le feedback et le contenu original
            generate_content_block_task.apply_async(
                args=[str(block.block_id)], # L'ID du bloc original à raffiner
                kwargs={'feedback': signal.feedback.model_dump(), 'is_refinement': True}, # Indique que c'est un raffinement
                queue='generation' # La tâche de raffinement est gérée par la queue de génération
            )
            logger.info(f"Projet {project_id}: Bloc {block.block_id} demande de raffinement par l'utilisateur. Tâche de raffinement déclenchée.")
            return project

        elif signal.signal_type == "ALL_APPROVED":
            # Signal pour assembler et exporter le document final
            if project.status != "completed": # S'assurer que le projet est dans un état où il peut être finalisé
                # Dans un cas réel, on vérifierait que tous les blocs sont 'validated'
                # ou que le projet est à la dernière étape du protocole
                raise BadRequestException(detail="Le projet n'est pas dans un état permettant l'approbation finale.")
            
            # Déclencher la tâche d'assemblage et d'exportation
            # Il faudrait récupérer le document_id/version_id du projet
            # Pour l'exemple, nous allons supposer qu'il y a un document principal lié au projet
            # et que l'exportation par défaut est le PDF.
            # (Cette logique serait plus robuste et récupérerait les formats depuis le projet)
            
            # Exemple: Récupérer le document principal du projet
            async with httpx.AsyncClient() as client:
                document_resp = await client.get(f"{self.persistence_service_url}/internal/documents/project/{project_id}")
                document_resp.raise_for_status()
                document_data = document_resp.json()
                document_id = document_data.get("document_id")
                current_version_id = document_data.get("current_version_id")

            if not current_version_id:
                raise NotFoundException(detail=f"Aucune version de document trouvée pour le projet {project_id}.")

            assemble_document_task.apply_async(
                args=[str(current_version_id)], 
                queue='export'
            )
            logger.info(f"Projet {project_id}: Signal ALL_APPROVED. Tâche d'assemblage et d'exportation déclenchée.")
            await self._update_project_status(project_id, "export_pending")
            return project

        else:
            raise BadRequestException(detail=f"Type de signal '{signal.signal_type}' non supporté en mode Supervisé.")

# Instancier la logique du superviseur
supervisor_logic = SupervisorLogic(
    persistence_service_url=settings.PERSISTENCE_SERVICE_URL
)
