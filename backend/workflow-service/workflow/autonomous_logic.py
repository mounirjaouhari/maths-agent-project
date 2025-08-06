# backend/workflow-service/workflow/autonomous_logic.py

import logging
from uuid import UUID
import httpx
from typing import Dict, Any, Optional

from shared.config import get_settings
from shared.exceptions import NotFoundException, BadRequestException, ServiceUnavailableException, InvalidWorkflowStateException
from shared.models import ProjectResponse, ContentBlockResponse, QCReport
from .state_machine import ContentBlockStateMachine, EVENTS
from ..tasks.workflow_tasks import (
    generate_content_block_task, 
    run_qc_task, 
    assemble_document_task, 
    export_document_task
) # Importe les tâches Celery pour l'orchestration

logger = logging.getLogger(__name__)
settings = get_settings()

class AutonomousLogic:
    """
    Implémente la logique spécifique au Mode Autonome du Moteur de Workflow.
    Gère l'auto-orchestration, l'auto-évaluation et l'auto-raffinement des tâches.
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

    async def _create_new_block_version_for_refinement(self, original_block: ContentBlockResponse, new_content_latex: str) -> ContentBlockResponse:
        """
        Crée une nouvelle version d'un bloc de contenu pour le raffinement,
        et archive l'ancienne version.
        Cette logique est simplifiée ici, dans un système réel, elle impliquerait
        le service de persistance pour gérer le versioning des documents.
        """
        async with httpx.AsyncClient() as client:
            # 1. Marquer l'ancien bloc comme archivé
            await self._update_block_status(original_block.block_id, "archived")

            # 2. Récupérer la version du document
            doc_version_resp = await client.get(f"{self.persistence_service_url}/internal/document-versions/{original_block.version_id}")
            doc_version_resp.raise_for_status()
            doc_version_data = doc_version_resp.json()

            # 3. Créer un nouveau bloc avec le contenu raffiné et l'ID de la même version
            new_block_data = original_block.model_dump(exclude_unset=True)
            new_block_data['block_id'] = str(UUID(int=0)) # Simule un nouvel UUID pour le nouveau bloc
            new_block_data['content_latex'] = new_content_latex
            new_block_data['status'] = "qc_pending" # Le nouveau bloc raffiné doit être re-QC
            new_block_data['refinement_attempts'] = original_block.refinement_attempts + 1
            new_block_data['created_at'] = None # Sera généré par la DB
            new_block_data['updated_at'] = None # Sera généré par la DB
            new_block_data['qc_report'] = None # Réinitialiser le rapport QC
            new_block_data['error_message'] = None # Réinitialiser le message d'erreur

            create_block_resp = await client.post(
                f"{self.persistence_service_url}/internal/content-blocks",
                json=new_block_data
            )
            create_block_resp.raise_for_status()
            new_block = ContentBlockResponse(**create_block_resp.json())
            logger.info(f"Nouvelle version du bloc {new_block.block_id} créée pour raffinement à partir de {original_block.block_id}")
            return new_block
            
    async def process_generated_block_result(self, project_id: UUID, block_id: UUID, qc_report: Dict = None):
        """
        Traite le résultat d'un bloc de contenu généré (après QC) en mode Autonome.
        Déclenche le raffinement si le QC échoue, ou marque le bloc comme validé.
        """
        project, block = await self._get_project_and_block(project_id, block_id)

        if project.mode != "Autonome":
            raise BadRequestException(detail=f"Le projet {project_id} n'est pas en mode Autonome.")

        if not block:
            raise NotFoundException(detail=f"Bloc {block_id} non trouvé pour le projet {project_id}.")

        fsm = ContentBlockStateMachine(
            initial_state=block.status, 
            mode=project.mode, 
            block_id=block.block_id, 
            project_id=project.project_id
        )

        qc_score = qc_report.get("overall_score", 0)
        qc_threshold = settings.QC_VALIDATION_THRESHOLD # Seuil de validation automatique
        max_refinement_attempts = settings.MAX_REFINEMENT_ATTEMPTS

        if qc_report.get("status") == "passed" and qc_score >= qc_threshold:
            # QC réussi et score suffisant, le bloc est validé automatiquement
            new_block_status = fsm.transition(EVENTS["QC_PASSED"])
            await self._update_block_status(block.block_id, new_block_status, qc_report=qc_report)
            logger.info(f"Projet {project_id}: Bloc {block_id} validé automatiquement (Score QC: {qc_score}).")
            # Déclencher la prochaine étape du plan autonome (ex: générer le bloc suivant)
            await self._advance_autonomous_plan(project_id)

        elif block.refinement_attempts < max_refinement_attempts:
            # QC échoué, et des tentatives de raffinement sont encore possibles
            new_block_status = fsm.transition(EVENTS["QC_FAILED"])
            await self._update_block_status(block.block_id, new_block_status, qc_report=qc_report)
            logger.info(f"Projet {project_id}: Bloc {block_id} QC échoué (Score QC: {qc_score}). Tentative de raffinement {block.refinement_attempts + 1}/{max_refinement_attempts}.")
            
            # Déclencher la tâche de raffinement via Celery
            # Le service d'interaction/raffinement prendra le rapport QC comme feedback
            # Nous créons une nouvelle version du bloc pour le raffinement
            new_block_for_refinement = await self._create_new_block_version_for_refinement(block, block.content_latex)

            generate_content_block_task.apply_async(
                args=[str(new_block_for_refinement.block_id)],
                kwargs={'feedback': qc_report, 'is_refinement': True}, # Passer le rapport QC comme feedback
                queue='generation' # La tâche de raffinement est gérée par la queue de génération
            )
            await self._update_block_status(new_block_for_refinement.block_id, EVENTS["REFINEMENT_STARTED"])


        else:
            # QC échoué et plus de tentatives de raffinement
            new_block_status = fsm.transition(EVENTS["REFINEMENT_FAILED"])
            await self._update_block_status(block.block_id, new_block_status, qc_report=qc_report, error_message="Max tentatives de raffinement atteintes.")
            logger.warning(f"Projet {project_id}: Bloc {block_id} a échoué au raffinement après {max_refinement_attempts} tentatives. Intervention manuelle requise.")
            # Notifier l'utilisateur (peut être une tâche Celery de notification)
            await self._advance_autonomous_plan(project_id) # Tente de passer au bloc suivant même en cas d'échec

    async def _advance_autonomous_plan(self, project_id: UUID):
        """
        Logique pour faire avancer le plan autonome du projet.
        Ceci est une version simplifiée. Dans un système réel, cela impliquerait
        la logique de planification (planner.py) pour déterminer le prochain bloc à générer.
        """
        project, _ = await self._get_project_and_block(project_id)

        # Pour l'exemple, nous allons juste vérifier si le projet est "terminé"
        # Dans un cas réel, on parcourrait la structure du document (content_structure)
        # pour trouver le prochain bloc 'pending_generation' ou 'qc_pending' à traiter.
        
        # Simuler la fin du plan si tous les blocs sont validés ou échoués
        async with httpx.AsyncClient() as client:
            # Récupérer la version actuelle du document
            document_resp = await client.get(f"{self.persistence_service_url}/internal/documents/project/{project_id}")
            document_resp.raise_for_status()
            document_data = document_resp.json()
            current_version_id = document_data.get("current_version_id")

            if not current_version_id:
                logger.warning(f"Projet {project_id}: Pas de version de document actuelle pour avancer le plan autonome.")
                return

            blocks_resp = await client.get(f"{self.persistence_service_url}/internal/content-blocks/version/{current_version_id}")
            blocks_resp.raise_for_status()
            blocks_data = blocks_resp.json()
            
            all_blocks_processed = True
            for block_data in blocks_data:
                block_status = block_data.get("status")
                if block_status not in ["validated", "generation_failed", "refinement_failed", "archived"]:
                    all_blocks_processed = False
                    break
            
            if all_blocks_processed:
                logger.info(f"Projet {project_id}: Tous les blocs ont été traités. Plan autonome terminé.")
                await self._update_project_status(project_id, "completed", "Plan autonome terminé")
                # Déclencher l'assemblage et l'exportation finale
                assemble_document_task.apply_async(args=[str(current_version_id)], queue='export')
                await self._update_project_status(project_id, "export_pending")
            else:
                # Logique pour trouver le prochain bloc à générer/traiter
                # Pour l'exemple, nous ne faisons rien ici, cela serait géré par un planificateur plus sophistiqué
                logger.info(f"Projet {project_id}: Plan autonome en cours. Prochain bloc à générer/traiter.")
                # Ici, on déclencherait la génération du prochain bloc si le projet est en 'in_progress'
                # et qu'il y a des blocs 'pending_generation'
                # Exemple:
                # next_pending_block = await self._get_next_pending_block_in_plan(project_id, current_version_id)
                # if next_pending_block:
                #     generate_content_block_task.apply_async(args=[str(next_pending_block.block_id)], queue='generation')
                #     await self._update_block_status(next_pending_block.block_id, EVENTS["GENERATE_STARTED"])


# Instancier la logique autonome
autonomous_logic = AutonomousLogic(
    persistence_service_url=settings.PERSISTENCE_SERVICE_URL
)
