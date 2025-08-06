# Fichier placeholder pour endpoints.py
# backend/workflow-service/api/internal/endpoints.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import logging
from uuid import UUID

from shared.config import get_settings
from shared.models import ProjectResponse, ContentBlockResponse, WorkflowSignal, QCReport
from shared.exceptions import NotFoundException, BadRequestException, ServiceUnavailableException, InvalidWorkflowStateException
from ..workflow.supervisor_logic import supervisor_logic # Importe la logique du mode supervisé
from ..workflow.autonomous_logic import autonomous_logic # Importe la logique du mode autonome
from ..workflow.state_manager import workflow_state_manager # Importe le gestionnaire d'état

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()

@router.post("/projects/{project_id}/signal", response_model=ProjectResponse, summary="Envoyer un signal au moteur de workflow (interne)")
async def handle_project_signal(
    project_id: str,
    signal: WorkflowSignal
):
    """
    Gère un signal reçu pour un projet spécifique.
    Principalement utilisé par l'API Gateway pour relayer les signaux utilisateur.
    """
    try:
        # Récupérer le projet pour déterminer le mode
        project = await workflow_state_manager.get_project_state(UUID(project_id))

        if project.mode == "Supervisé":
            updated_project = await supervisor_logic.handle_user_signal(UUID(project_id), signal)
            return updated_project
        elif project.mode == "Autonome":
            # Les signaux utilisateur en mode autonome sont généralement pour des révisions globales
            # ou des actions de fin de projet. La logique serait dans autonomous_logic.
            # Pour l'instant, on peut lever une erreur si le signal n'est pas "ALL_APPROVED"
            if signal.signal_type == "ALL_APPROVED":
                # La logique de finalisation est déjà gérée par autonomous_logic.process_generated_block_result
                # si tous les blocs sont traités. Ce signal pourrait servir à forcer l'exportation.
                logger.info(f"Projet {project_id} en mode Autonome a reçu le signal ALL_APPROVED. Déclenchement de l'exportation finale.")
                # Récupérer la version actuelle du document
                document_resp = await httpx.AsyncClient().get(f"{settings.PERSISTENCE_SERVICE_URL}/internal/documents/project/{project_id}")
                document_resp.raise_for_status()
                document_data = document_resp.json()
                current_version_id = document_data.get("current_version_id")

                if not current_version_id:
                    raise NotFoundException(detail=f"Aucune version de document trouvée pour le projet {project_id}.")

                from ..tasks.workflow_tasks import assemble_document_task
                assemble_document_task.delay(str(current_version_id))
                await workflow_state_manager.update_project_state(UUID(project_id), "export_pending")
                return project
            else:
                raise BadRequestException(detail=f"Le signal '{signal.signal_type}' n'est pas supporté en mode Autonome pour cet endpoint.")
        else:
            raise BadRequestException(detail=f"Mode de projet inconnu: {project.mode}")

    except NotFoundException:
        raise
    except BadRequestException:
        raise
    except ServiceUnavailableException:
        raise
    except InvalidWorkflowStateException as e:
        raise BadRequestException(detail=e.detail)
    except httpx.HTTPStatusError as e:
        logger.error(f"Erreur HTTP lors de l'appel à un service dépendant: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Erreur du service dépendant: {e.response.text}")
    except Exception as e:
        logger.critical(f"Erreur inattendue lors du traitement du signal pour le projet {project_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur.")

@router.post("/tasks/{task_id}/complete", status_code=status.HTTP_200_OK, summary="Marquer une tâche de workflow comme terminée (interne)")
async def complete_workflow_task(
    task_id: str,
    result_data: Dict[str, Any] # Contient 'success', 'result', 'error_message'
):
    """
    Endpoint interne pour marquer une tâche de workflow comme terminée.
    Utilisé par les workers Celery pour rapporter l'achèvement d'une tâche.
    """
    try:
        # Récupérer la tâche de workflow
        task = await workflow_state_manager.get_workflow_task_state(UUID(task_id)) # Cette méthode n'existe pas encore, à ajouter
        if not task:
            raise NotFoundException(detail=f"Tâche de workflow avec l'ID {task_id} non trouvée.")

        # Mettre à jour le statut de la tâche
        new_status = "completed" if result_data.get("success", False) else "failed"
        error_message = result_data.get("error_message")

        await workflow_state_manager.update_workflow_task_state(
            UUID(task_id), 
            {"status": new_status, "completed_at": datetime.now(timezone.utc), "error_message": error_message}
        )
        logger.info(f"Tâche de workflow {task_id} marquée comme {new_status}.")

        # Logique pour traiter le résultat de la tâche et faire avancer le workflow
        # Cela dépend du type de tâche et du mode du projet
        project = await workflow_state_manager.get_project_state(task.project_id)

        if task.task_type == "generate_block" or task.task_type == "refine_block":
            block_id = task.parameters.get("block_id")
            qc_report_data = result_data.get("result", {}).get("qc_report") # Si le résultat inclut le rapport QC
            
            if project.mode == "Autonome":
                await autonomous_logic.process_generated_block_result(project.project_id, UUID(block_id), qc_report_data)
            elif project.mode == "Supervisé":
                # En mode supervisé, la fin de génération/raffinement mène à QC_PENDING puis PENDING_VALIDATION
                # Le statut du bloc est déjà mis à jour par la tâche Celery elle-même
                logger.info(f"Bloc {block_id} généré/raffiné. Attente de la validation utilisateur en mode Supervisé.")
        
        elif task.task_type == "run_qc":
            block_id = task.parameters.get("block_id")
            qc_report_data = result_data.get("result", {}).get("qc_report")
            
            if project.mode == "Autonome":
                await autonomous_logic.process_generated_block_result(project.project_id, UUID(block_id), qc_report_data)
            elif project.mode == "Supervisé":
                # La logique de supervisor_logic.handle_user_signal gère les transitions post-QC
                # Ici, on s'assure juste que le rapport QC est à jour sur le bloc
                logger.info(f"QC pour bloc {block_id} terminé. Le projet est en mode Supervisé.")
        
        elif task.task_type == "assemble_document":
            document_version_id = task.parameters.get("document_version_id")
            if result_data.get("success", False):
                await workflow_state_manager.update_project_state(project.project_id, "assembled")
                logger.info(f"Document version {document_version_id} assemblé. Projet {project.project_id} mis à jour.")
            else:
                await workflow_state_manager.update_project_state(project.project_id, "assembly_failed", error_message=error_message)
                logger.error(f"Assemblage du document version {document_version_id} échoué. Projet {project.project_id} mis à jour en échec.")
        
        elif task.task_type == "export_document":
            document_version_id = task.parameters.get("document_version_id")
            if result_data.get("success", False):
                await workflow_state_manager.update_project_state(project.project_id, "completed_exported")
                logger.info(f"Document version {document_version_id} exporté. Projet {project.project_id} mis à jour en 'completed_exported'.")
            else:
                await workflow_state_manager.update_project_state(project.project_id, "export_failed", error_message=error_message)
                logger.error(f"Exportation du document version {document_version_id} échoué. Projet {project.project_id} mis à jour en échec.")

    except NotFoundException:
        raise
    except BadRequestException:
        raise
    except ServiceUnavailableException:
        raise
    except Exception as e:
        logger.critical(f"Erreur inattendue lors du traitement de la fin de tâche {task_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur.")

