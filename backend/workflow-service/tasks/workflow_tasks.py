# Fichier placeholder pour workflow_tasks.py
# backend/workflow-service/tasks/workflow_tasks.py

from celery import Celery
import httpx
import logging
from typing import Dict, Any, Optional
from uuid import UUID

from shared.config import get_settings
from shared.exceptions import (
    LLMGenerationError, QCAnalysisError, ExternalToolError,
    DocumentAssemblyError, DocumentExportError, ServiceUnavailableException
)
from shared.models import ContentBlockResponse, ProjectResponse, QCReport
from ..workflow.state_manager import workflow_state_manager # Importe le gestionnaire d'état
from ..workflow.state_machine import EVENTS # Importe les événements pour les transitions
from ..workflow.autonomous_logic import autonomous_logic # Pour le traitement des résultats en mode autonome

# Configure le logger
logger = logging.getLogger(__name__)

# Initialisation de l'application Celery
# Le broker et le backend des résultats sont configurés via les variables d'environnement
celery_app = Celery(
    'math_agent_tasks',
    broker=get_settings().CELERY_BROKER_URL,
    backend=get_settings().CELERY_RESULT_BACKEND
)

# Configuration de Celery (peut être aussi dans config.py)
celery_app.conf.update(
    task_serializer=get_settings().CELERY_TASK_SERIALIZER,
    accept_content=get_settings().CELERY_ACCEPT_CONTENT,
    result_serializer=get_settings().CELERY_RESULT_SERIALIZER,
    timezone=get_settings().CELERY_TIMEZONE,
    enable_utc=get_settings().CELERY_ENABLE_UTC,
    task_acks_late=True, # Les tâches sont acquittées après exécution, pas avant
    worker_prefetch_multiplier=1, # Ne pas pré-charger trop de tâches
    task_track_started=True, # Permet de suivre l'état 'STARTED'
    task_queues={
        'default': {'exchange': 'default', 'routing_key': 'default'},
        'general': {'exchange': 'general', 'routing_key': 'general'},
        'generation': {'exchange': 'generation', 'routing_key': 'generation'},
        'qc': {'exchange': 'qc', 'routing_key': 'qc'},
        'export': {'exchange': 'export', 'routing_key': 'export'},
    },
    task_routes={
        'workflow_tasks.generate_content_block_task': {'queue': 'generation'},
        'workflow_tasks.run_qc_task': {'queue': 'qc'},
        'workflow_tasks.refine_content_block_task': {'queue': 'generation'}, # Le raffinement utilise le service de génération
        'workflow_tasks.assemble_document_task': {'queue': 'export'},
        'workflow_tasks.export_document_task': {'queue': 'export'},
    },
    task_annotations={
        'workflow_tasks.generate_content_block_task': {'rate_limit': '10/s'}, # Exemple de limite de taux
        'workflow_tasks.run_qc_task': {'rate_limit': '5/s'},
    }
)

@celery_app.task(bind=True, max_retries=get_settings().MAX_REFINEMENT_ATTEMPTS, default_retry_delay=60)
async def generate_content_block_task(self, block_id: str, feedback: Optional[Dict] = None, is_refinement: bool = False):
    """
    Tâche Celery pour générer le contenu d'un bloc spécifique ou le raffiner.
    Args:
        block_id (str): L'ID du bloc de contenu à générer/raffiner.
        feedback (Optional[Dict]): Le feedback pour le raffinement (rapport QC ou feedback utilisateur).
        is_refinement (bool): Indique si c'est une tâche de raffinement.
    """
    settings = get_settings()
    current_block = None
    try:
        current_block = await workflow_state_manager.get_content_block_state(UUID(block_id))
        project = await workflow_state_manager.get_project_state(current_block.project_id) # Assurez-vous que project_id est accessible via le bloc ou sa version

        # Mettre à jour le statut du bloc pour indiquer que la génération/raffinement est en cours
        await workflow_state_manager.update_content_block_state(
            UUID(block_id), {"status": EVENTS["GENERATE_STARTED"] if not is_refinement else EVENTS["REFINEMENT_STARTED"]}
        )
        
        async with httpx.AsyncClient() as client:
            if is_refinement:
                logger.info(f"Raffinement du bloc {block_id} (tentative {current_block.refinement_attempts + 1})...")
                # Appel au service d'interaction/raffinement
                response = await client.post(
                    f"{settings.INTERACTION_SERVICE_URL}/internal/refine/content",
                    json={
                        "content_latex": current_block.content_latex,
                        "feedback": feedback,
                        "block_type": current_block.block_type,
                        "level": project.level, # Supposons que le niveau est sur le projet
                        "style": project.style, # Supposons que le style est sur le projet
                        "context": {} # Ajouter un contexte plus riche si nécessaire
                    },
                    timeout=300.0 # Temps d'attente pour la réponse (peut être long pour les LLMs)
                )
            else:
                logger.info(f"Génération du bloc {block_id}...")
                # Appel au service de génération
                # Les paramètres de génération dépendent du type de bloc et du contexte
                # C'est une simplification, en réalité, on construirait la requête en fonction du block_type
                response = await client.post(
                    f"{settings.GENERATION_SERVICE_URL}/internal/generate/text-block", # Exemple générique
                    json={
                        "block_type": current_block.block_type,
                        "level": project.level,
                        "style": project.style,
                        "section_context": {}, # Ajouter le contexte de la section
                        "concept_id": None # Ajouter l'ID du concept si applicable
                    },
                    timeout=300.0
                )
            
            response.raise_for_status()
            generated_content = response.json().get("content_latex")

        # Mettre à jour le bloc avec le contenu généré et le statut 'qc_pending'
        # La FSM du bloc sera mise à jour par le processus qui reçoit le résultat de cette tâche
        # Ici, nous mettons à jour la DB directement pour indiquer le succès
        await workflow_state_manager.update_content_block_state(
            UUID(block_id), 
            {
                "content_latex": generated_content,
                "status": EVENTS["GENERATE_SUCCESS"] if not is_refinement else EVENTS["REFINEMENT_SUCCESS"], # Statut intermédiaire
                "source_llm": "unknown", # Le service de génération devrait retourner le LLM utilisé
                "generation_params": {} # Le service de génération devrait retourner les params
            }
        )
        logger.info(f"Bloc {block_id} {'raffiné' if is_refinement else 'généré'} avec succès. Déclenchement du QC.")
        
        # Déclencher la tâche QC pour ce bloc
        run_qc_task.delay(block_id)

    except httpx.HTTPStatusError as e:
        error_detail = e.response.text
        status_code = e.response.status_code
        logger.error(f"HTTP Error calling {'Interaction' if is_refinement else 'Generation'} Service for block {block_id}: {status_code} - {error_detail}")
        # Marquer le bloc comme échoué
        await workflow_state_manager.update_content_block_state(
            UUID(block_id), 
            {
                "status": EVENTS["GENERATION_FAILED"] if not is_refinement else EVENTS["REFINEMENT_FAILED"],
                "error_message": f"Service error ({status_code}): {error_detail}"
            }
        )
        # Tenter un retry si l'erreur est transitoire (ex: 5xx, ou spécifique à l'API LLM)
        if status_code >= 500 or "rate limit" in error_detail.lower():
            raise self.retry(exc=e, countdown=60) # Réessayer dans 60 secondes
        raise LLMGenerationError(detail=f"Échec de la {'génération' if not is_refinement else 'raffinement'} du contenu: {error_detail}")
    except httpx.RequestError as e:
        logger.error(f"Network Error calling {'Interaction' if is_refinement else 'Generation'} Service for block {block_id}: {e}")
        await workflow_state_manager.update_content_block_state(
            UUID(block_id), 
            {
                "status": EVENTS["GENERATION_FAILED"] if not is_refinement else EVENTS["REFINEMENT_FAILED"],
                "error_message": f"Network error: {e}"
            }
        )
        raise self.retry(exc=e, countdown=60) # Réessayer en cas d'erreur réseau
    except Exception as e:
        logger.critical(f"Unhandled exception in generate_content_block_task for block {block_id}: {e}", exc_info=True)
        await workflow_state_manager.update_content_block_state(
            UUID(block_id), 
            {
                "status": EVENTS["CRITICAL_FAIL"],
                "error_message": f"Erreur interne inattendue: {e}"
            }
        )
        raise # Re-lève l'exception pour que Celery la marque comme échouée

@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
async def run_qc_task(self, block_id: str):
    """
    Tâche Celery pour exécuter le contrôle qualité sur un bloc de contenu.
    """
    settings = get_settings()
    current_block = None
    try:
        current_block = await workflow_state_manager.get_content_block_state(UUID(block_id))
        project = await workflow_state_manager.get_project_state(current_block.project_id) # Assurez-vous que project_id est accessible via le bloc ou sa version

        await workflow_state_manager.update_content_block_state(
            UUID(block_id), {"status": EVENTS["QC_STARTED"]}
        )

        async with httpx.AsyncClient() as client:
            # Appel au service QC
            response = await client.post(
                f"{settings.QC_SERVICE_URL}/internal/analyze/content-block",
                json={
                    "block_id": str(block_id),
                    "content_latex": current_block.content_latex,
                    "block_type": current_block.block_type,
                    "level": project.level,
                    "style": project.style,
                    "context": {} # Ajouter un contexte plus riche si nécessaire
                },
                timeout=180.0 # Temps d'attente pour la réponse QC
            )
            response.raise_for_status()
            qc_report_data = response.json()
            qc_report = QCReport(**qc_report_data)

        # Mettre à jour le bloc avec le rapport QC et le statut approprié
        # La logique de transition est gérée par le autonomous_logic ou supervisor_logic
        await workflow_state_manager.update_content_block_state(
            UUID(block_id), 
            {
                "qc_report": qc_report.model_dump(),
                "status": EVENTS["QC_PASSED"] if qc_report.status == "passed" else EVENTS["QC_FAILED"]
            }
        )
        logger.info(f"Bloc {block_id} QC terminé. Statut: {qc_report.status}, Score: {qc_report.overall_score}")

        # Si en mode autonome, déclencher la logique de progression
        if project.mode == "Autonome":
            await autonomous_logic.process_generated_block_result(project.project_id, UUID(block_id), qc_report_data)
        # En mode Supervisé, le Moteur de Workflow attendra un signal utilisateur
        
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text
        status_code = e.response.status_code
        logger.error(f"HTTP Error calling QC Service for block {block_id}: {status_code} - {error_detail}")
        await workflow_state_manager.update_content_block_state(
            UUID(block_id), 
            {
                "status": EVENTS["QC_FAILED"], # Marquer comme QC failed si le service QC lui-même échoue
                "error_message": f"Service QC error ({status_code}): {error_detail}"
            }
        )
        if status_code >= 500: # Réessayer en cas d'erreur serveur
            raise self.retry(exc=e, countdown=30)
        raise QCAnalysisError(detail=f"Échec de l'analyse QC: {error_detail}")
    except httpx.RequestError as e:
        logger.error(f"Network Error calling QC Service for block {block_id}: {e}")
        await workflow_state_manager.update_content_block_state(
            UUID(block_id), 
            {
                "status": EVENTS["QC_FAILED"],
                "error_message": f"Network error during QC: {e}"
            }
        )
        raise self.retry(exc=e, countdown=30)
    except Exception as e:
        logger.critical(f"Unhandled exception in run_qc_task for block {block_id}: {e}", exc_info=True)
        await workflow_state_manager.update_content_block_state(
            UUID(block_id), 
            {
                "status": EVENTS["CRITICAL_FAIL"],
                "error_message": f"Erreur interne inattendue lors du QC: {e}"
            }
        )
        raise

# Note: refine_content_block_task est fusionnée avec generate_content_block_task pour simplifier
# car le service de génération/raffinement est appelé de manière similaire.
# Cependant, si le service de raffinement est distinct, cette tâche serait séparée.
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
async def assemble_document_task(self, document_version_id: str):
    """
    Tâche Celery pour assembler le document final à partir d'une version de document.
    """
    settings = get_settings()
    try:
        logger.info(f"Assemblage du document version {document_version_id}...")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.ASSEMBLY_EXPORT_SERVICE_URL}/internal/assemble/document/{document_version_id}",
                timeout=600.0 # L'assemblage peut être long
            )
            response.raise_for_status()
            assembly_result = response.json()
            
            # Mettre à jour le statut du document/projet si nécessaire
            # (Le service d'assemblage peut retourner l'ID du document assemblé ou un statut)
            # Pour l'exemple, nous allons juste logger le succès
            logger.info(f"Document version {document_version_id} assemblé avec succès. Résultat: {assembly_result}")

            # Déclencher l'exportation par défaut (ex: PDF)
            export_document_task.delay(document_version_id, ["pdf"])

    except httpx.HTTPStatusError as e:
        error_detail = e.response.text
        status_code = e.response.status_code
        logger.error(f"HTTP Error calling Assembly Service for document version {document_version_id}: {status_code} - {error_detail}")
        # Mettre à jour le statut du projet ou du document en erreur
        # (Nécessite de récupérer le project_id depuis document_version_id)
        # await workflow_state_manager.update_project_status(project_id, EVENTS["CRITICAL_FAIL"], error_message=f"Assembly failed: {error_detail}")
        raise DocumentAssemblyError(detail=f"Échec de l'assemblage du document: {error_detail}")
    except httpx.RequestError as e:
        logger.error(f"Network Error calling Assembly Service for document version {document_version_id}: {e}")
        raise self.retry(exc=e, countdown=60)
    except Exception as e:
        logger.critical(f"Unhandled exception in assemble_document_task for document version {document_version_id}: {e}", exc_info=True)
        raise

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
async def export_document_task(self, document_version_id: str, formats: List[str]):
    """
    Tâche Celery pour exporter le document dans un ou plusieurs formats spécifiques.
    """
    settings = get_settings()
    try:
        logger.info(f"Exportation du document version {document_version_id} aux formats {formats}...")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.ASSEMBLY_EXPORT_SERVICE_URL}/internal/export/document/{document_version_id}",
                json={"formats": formats},
                timeout=900.0 # L'exportation peut être très longue (compilation PDF)
            )
            response.raise_for_status()
            export_result = response.json()
            
            logger.info(f"Document version {document_version_id} exporté avec succès. Résultat: {export_result}")
            # Ici, on pourrait mettre à jour le projet/document avec les URLs des fichiers exportés
            # (Nécessite de récupérer le project_id depuis document_version_id)
            # await workflow_state_manager.update_project_status(project_id, "completed_exported")

    except httpx.HTTPStatusError as e:
        error_detail = e.response.text
        status_code = e.response.status_code
        logger.error(f"HTTP Error calling Export Service for document version {document_version_id}: {status_code} - {error_detail}")
        raise DocumentExportError(detail=f"Échec de l'exportation du document: {error_detail}")
    except httpx.RequestError as e:
        logger.error(f"Network Error calling Export Service for document version {document_version_id}: {e}")
        raise self.retry(exc=e, countdown=60)
    except Exception as e:
        logger.critical(f"Unhandled exception in export_document_task for document version {document_version_id}: {e}", exc_info=True)
        raise

