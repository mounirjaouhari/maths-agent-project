# backend/workflow-service/workflow/transitions.py

import logging
from typing import Dict, Any, Callable, List
from uuid import UUID

from shared.exceptions import InvalidWorkflowStateException
from shared.models import ProjectResponse, ContentBlockResponse
from .state_machine import ContentBlockStateMachine, EVENTS, BLOCK_STATES # Importe les définitions d'états et d'événements

logger = logging.getLogger(__name__)

# Ce fichier définira les transitions et les actions.
# Dans une implémentation plus sophistiquée, on pourrait utiliser une bibliothèque comme 'transitions'.
# Pour l'instant, nous allons définir une structure pour les actions de transition.

# Un dictionnaire pour mapper les transitions (état_source, événement) -> (état_cible, fonction_action)
# La fonction_action prendrait en paramètres l'instance de la FSM, les données de l'entité, et les kwargs de l'événement.

# Exemple de structure pour les actions de transition
# Ces fonctions seraient appelées par la logique de transition dans state_machine.py
# ou directement par supervisor_logic.py / autonomous_logic.py

async def action_generate_success(fsm: ContentBlockStateMachine, block: ContentBlockResponse, **kwargs):
    """Action exécutée après une génération réussie."""
    logger.info(f"Action: Génération réussie pour le bloc {fsm.block_id}. Déclenchement du QC.")
    # Ici, on déclencherait la tâche Celery pour le QC
    # from ..tasks.workflow_tasks import run_qc_task
    # run_qc_task.delay(str(fsm.block_id))
    pass

async def action_qc_passed_autonomous(fsm: ContentBlockStateMachine, block: ContentBlockResponse, qc_report: Dict, **kwargs):
    """Action exécutée après un QC réussi en mode Autonome."""
    logger.info(f"Action: Bloc {fsm.block_id} validé automatiquement (Score QC: {qc_report.get('overall_score')}).")
    # Mettre à jour le statut du bloc et le rapport QC via le service de persistance
    # await _update_block_status(fsm.block_id, fsm.get_current_state(), qc_report=qc_report)
    # Logique pour avancer le plan autonome (gérée par autonomous_logic)
    pass

async def action_qc_passed_supervised(fsm: ContentBlockStateMachine, block: ContentBlockResponse, qc_report: Dict, **kwargs):
    """Action exécutée après un QC réussi en mode Supervisé."""
    logger.info(f"Action: Bloc {fsm.block_id} QC réussi (Score QC: {qc_report.get('overall_score')}). En attente de validation utilisateur.")
    # Mettre à jour le statut du bloc et le rapport QC via le service de persistance
    # await _update_block_status(fsm.block_id, fsm.get_current_state(), qc_report=qc_report)
    # Notifier le frontend que le bloc est prêt pour validation (non implémenté ici directement)
    pass

async def action_qc_failed(fsm: ContentBlockStateMachine, block: ContentBlockResponse, qc_report: Dict, **kwargs):
    """Action exécutée après un QC échoué."""
    logger.info(f"Action: Bloc {fsm.block_id} QC échoué (Score QC: {qc_report.get('overall_score')}). Raffinement nécessaire.")
    # Mettre à jour le statut du bloc et le rapport QC via le service de persistance
    # await _update_block_status(fsm.block_id, fsm.get_current_state(), qc_report=qc_report)
    # La logique de déclenchement du raffinement est dans autonomous_logic ou supervisor_logic
    pass

async def action_user_validate(fsm: ContentBlockStateMachine, block: ContentBlockResponse, **kwargs):
    """Action exécutée après validation utilisateur."""
    logger.info(f"Action: Bloc {fsm.block_id} validé par l'utilisateur.")
    # Mettre à jour le statut du bloc via le service de persistance
    # await _update_block_status(fsm.block_id, fsm.get_current_state())
    pass

async def action_user_redo(fsm: ContentBlockStateMachine, block: ContentBlockResponse, user_feedback: Dict, **kwargs):
    """Action exécutée après demande de raffinement par l'utilisateur."""
    logger.info(f"Action: Bloc {fsm.block_id} demande de raffinement par l'utilisateur avec feedback.")
    # Mettre à jour le statut du bloc via le service de persistance
    # await _update_block_status(fsm.block_id, fsm.get_current_state())
    # Déclencher la tâche de raffinement via Celery
    # from ..tasks.workflow_tasks import refine_content_block_task
    # refine_content_block_task.apply_async(args=[str(block.block_id)], kwargs={'feedback': user_feedback, 'is_refinement': True}, queue='generation')
    pass

async def action_refinement_success(fsm: ContentBlockStateMachine, block: ContentBlockResponse, **kwargs):
    """Action exécutée après un raffinement réussi."""
    logger.info(f"Action: Bloc {fsm.block_id} raffiné avec succès. Re-soumission au QC.")
    # Mettre à jour le statut du bloc via le service de persistance
    # await _update_block_status(fsm.block_id, fsm.get_current_state())
    # from ..tasks.workflow_tasks import run_qc_task
    # run_qc_task.delay(str(fsm.block_id))
    pass

async def action_failed_state(fsm: ContentBlockStateMachine, block: ContentBlockResponse, error_message: str, **kwargs):
    """Action exécutée lorsqu'un bloc atteint un état d'échec (génération, raffinement, critique)."""
    logger.error(f"Action: Bloc {fsm.block_id} en état d'échec '{fsm.get_current_state()}'. Message: {error_message}")
    # Mettre à jour le statut du bloc et le message d'erreur via le service de persistance
    # await _update_block_status(fsm.block_id, fsm.get_current_state(), error_message=error_message)
    # Potentiellement, notifier l'utilisateur ou l'administrateur
    pass


# Dictionnaire des actions de transition
# Chaque clé est un tuple (état_source, événement)
# La valeur est un tuple (état_cible, fonction_action_asynchrone)
# Note: La logique de sélection de l'état cible est déjà dans ContentBlockStateMachine._get_allowed_transitions
# Ce dictionnaire se concentre sur les actions à exécuter.
TRANSITION_ACTIONS: Dict[tuple[str, str], Callable] = {
    ("generation_in_progress", EVENTS["GENERATE_SUCCESS"]): action_generate_success,
    ("qc_in_progress", EVENTS["QC_PASSED"]): None, # L'action dépendra du mode (voir ci-dessous)
    ("qc_in_progress", EVENTS["QC_FAILED"]): action_qc_failed,
    ("pending_validation", EVENTS["USER_VALIDATE"]): action_user_validate,
    ("pending_validation", EVENTS["USER_REDO"]): action_user_redo,
    ("refinement_in_progress", EVENTS["REFINEMENT_SUCCESS"]): action_refinement_success,
    
    # Actions pour les états d'échec
    ("generation_in_progress", EVENTS["GENERATE_FAILED"]): action_failed_state,
    ("refinement_in_progress", EVENTS["REFINEMENT_FAILED"]): action_failed_state,
    ("generation_in_progress", EVENTS["CRITICAL_FAIL"]): action_failed_state,
    ("qc_in_progress", EVENTS["CRITICAL_FAIL"]): action_failed_state,
    ("refinement_in_progress", EVENTS["CRITICAL_FAIL"]): action_failed_state,
}

# Actions spécifiques au mode pour QC_PASSED
async def get_qc_passed_action(fsm: ContentBlockStateMachine, block: ContentBlockResponse, qc_report: Dict, **kwargs):
    if fsm.mode == "Autonome":
        return await action_qc_passed_autonomous(fsm, block, qc_report, **kwargs)
    elif fsm.mode == "Supervisé":
        return await action_qc_passed_supervised(fsm, block, qc_report, **kwargs)
    else:
        logger.error(f"Mode inconnu pour QC_PASSED: {fsm.mode}")


# La fonction d'exécution des actions serait appelée par la logique de transition
async def execute_transition_action(fsm: ContentBlockStateMachine, block: ContentBlockResponse, event: str, **kwargs):
    """
    Exécute l'action associée à une transition spécifique.
    """
    action_func = None
    if (fsm.current_state, event) in TRANSITION_ACTIONS:
        action_func = TRANSITION_ACTIONS[(fsm.current_state, event)]
    
    # Gérer le cas spécifique de QC_PASSED où l'action dépend du mode
    if fsm.current_state == "qc_in_progress" and event == EVENTS["QC_PASSED"]:
        await get_qc_passed_action(fsm, block, kwargs.get('qc_report'))
        return

    if action_func:
        # Les actions sont asynchrones, donc on les attend
        await action_func(fsm, block, **kwargs)
    else:
        logger.debug(f"Aucune action spécifique définie pour la transition {fsm.current_state} -> {fsm.get_current_state()} via {event}")

