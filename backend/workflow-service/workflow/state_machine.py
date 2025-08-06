# Fichier placeholder pour state_machine.py
# backend/workflow-service/workflow/state_machine.py

from typing import Dict, Any, Callable, List
import logging
from uuid import UUID

from shared.exceptions import InvalidWorkflowStateException

logger = logging.getLogger(__name__)

# Définition des états possibles pour un bloc de contenu
# Ces états doivent correspondre à ceux définis dans le modèle ContentBlockResponse de shared/models.py
BLOCK_STATES = [
    "pending_generation",       # En attente de génération initiale
    "generation_in_progress",   # Génération en cours
    "generation_failed",        # Génération échouée
    "qc_pending",               # En attente de contrôle qualité
    "qc_in_progress",           # Contrôle qualité en cours
    "qc_failed",                # Contrôle qualité échoué (problèmes détectés)
    "qc_passed",                # Contrôle qualité réussi
    "refinement_pending",       # En attente de raffinement
    "refinement_in_progress",   # Raffinement en cours
    "refinement_failed",        # Raffinement échoué
    "pending_validation",       # En attente de validation utilisateur (Mode Supervisé)
    "validated",                # Validé (par l'utilisateur ou automatiquement)
    "archived",                 # Archivé (ancienne version d'un bloc)
    "critical_error"            # Erreur critique non récupérable
]

# Définition des événements qui peuvent déclencher des transitions
EVENTS = {
    "GENERATE_STARTED": "Génération démarrée",
    "GENERATE_SUCCESS": "Génération réussie",
    "GENERATE_FAILED": "Génération échouée",
    "QC_STARTED": "QC démarré",
    "QC_PASSED": "QC réussi",
    "QC_FAILED": "QC échoué",
    "REFINEMENT_NEEDED": "Raffinement nécessaire",
    "REFINEMENT_STARTED": "Raffinement démarré",
    "REFINEMENT_SUCCESS": "Raffinement réussi",
    "REFINEMENT_FAILED": "Raffinement échouée",
    "USER_VALIDATE": "Validation utilisateur",
    "USER_REDO": "Demande de raffinement par l'utilisateur",
    "ARCHIVE": "Archivage du bloc",
    "CRITICAL_FAIL": "Échec critique"
}

class ContentBlockStateMachine:
    """
    Implémentation d'une Machine à États Finis (FSM) pour un bloc de contenu.
    Gère les transitions d'états et les actions associées en fonction des événements
    et du mode de fonctionnement (Supervisé/Autonome).
    """
    def __init__(self, initial_state: str, mode: str, block_id: UUID, project_id: UUID):
        if initial_state not in BLOCK_STATES:
            raise ValueError(f"État initial '{initial_state}' invalide.")
        self.current_state = initial_state
        self.mode = mode # 'Supervisé' ou 'Autonome'
        self.block_id = block_id
        self.project_id = project_id
        logger.info(f"FSM Block {self.block_id} initialisée en état '{self.current_state}' (Mode: {self.mode})")

    def _get_allowed_transitions(self, event: str) -> List[str]:
        """
        Retourne la liste des états cibles possibles pour un événement donné
        depuis l'état actuel, en fonction du mode.
        """
        transitions = {
            "pending_generation": {
                "GENERATE_STARTED": "generation_in_progress"
            },
            "generation_in_progress": {
                "GENERATE_SUCCESS": "qc_pending",
                "GENERATE_FAILED": "generation_failed",
                "CRITICAL_FAIL": "critical_error"
            },
            "generation_failed": {
                "ARCHIVE": "archived" # Potentiellement, l'utilisateur archive l'échec
            },
            "qc_pending": {
                "QC_STARTED": "qc_in_progress"
            },
            "qc_in_progress": {
                "QC_PASSED": "qc_passed",
                "QC_FAILED": "qc_failed",
                "CRITICAL_FAIL": "critical_error"
            },
            "qc_passed": {
                "USER_VALIDATE": "validated", # Mode Supervisé
                "ARCHIVE": "archived", # Si une nouvelle version est créée
                "REFINEMENT_NEEDED": "refinement_pending" # Peut être déclenché par le système pour des améliorations non critiques
            },
            "qc_failed": {
                "REFINEMENT_NEEDED": "refinement_pending",
                "USER_REDO": "refinement_pending" # Mode Supervisé
            },
            "refinement_pending": {
                "REFINEMENT_STARTED": "refinement_in_progress"
            },
            "refinement_in_progress": {
                "REFINEMENT_SUCCESS": "qc_pending", # Après raffinement, le bloc doit être re-QC
                "REFINEMENT_FAILED": "refinement_failed",
                "CRITICAL_FAIL": "critical_error"
            },
            "refinement_failed": {
                "ARCHIVE": "archived" # Potentiellement, l'utilisateur archive l'échec
            },
            "pending_validation": { # Spécifique au mode Supervisé
                "USER_VALIDATE": "validated",
                "USER_REDO": "refinement_pending"
            },
            "validated": {
                "ARCHIVE": "archived" # Quand une nouvelle version est créée à partir de celle-ci
            },
            "critical_error": {
                "ARCHIVE": "archived"
            }
        }
        
        # Logique de transition spécifique au mode
        if self.mode == "Supervisé":
            if self.current_state == "qc_passed" and event == "QC_PASSED":
                return ["pending_validation"] # Passe à l'attente de validation utilisateur
            if self.current_state == "qc_failed" and event == "QC_FAILED":
                return ["refinement_pending"] # Le QC échoué en supervisé peut nécessiter un raffinement utilisateur
            
        elif self.mode == "Autonome":
            if self.current_state == "qc_passed" and event == "QC_PASSED":
                return ["validated"] # Validation automatique
            if self.current_state == "qc_failed" and event == "QC_FAILED":
                return ["refinement_pending"] # Raffinement automatique
            
        # Retourne l'état cible pour l'événement donné, ou une liste vide si aucune transition n'est définie
        next_state = transitions.get(self.current_state, {}).get(event)
        return [next_state] if next_state else []

    def transition(self, event: str, **kwargs) -> str:
        """
        Tente de faire transiter la FSM vers un nouvel état en réponse à un événement.
        Args:
            event (str): L'événement qui déclenche la transition.
            **kwargs: Arguments supplémentaires pour les actions de transition.
        Returns:
            str: Le nouvel état après la transition.
        Raises:
            InvalidWorkflowStateException: Si l'événement n'est pas permis dans l'état actuel.
        """
        allowed_next_states = self._get_allowed_transitions(event)

        if not allowed_next_states:
            raise InvalidWorkflowStateException(
                current_status=self.current_state,
                attempted_action=f"Événement '{event}' non permis."
            )
        
        # Pour cette implémentation simple, nous prenons le premier état autorisé.
        # Dans une implémentation plus complexe avec des conditions, il faudrait choisir
        # l'état cible basé sur ces conditions.
        new_state = allowed_next_states[0] 
        
        old_state = self.current_state
        self.current_state = new_state
        logger.info(f"FSM Block {self.block_id}: Transition de '{old_state}' vers '{self.current_state}' via événement '{event}' (Mode: {self.mode})")
        
        # Ici, vous déclencheriez les actions associées à la transition
        self._execute_transition_actions(old_state, new_state, event, **kwargs)
        
        return self.current_state

    def _execute_transition_actions(self, old_state: str, new_state: str, event: str, **kwargs):
        """
        Exécute les actions associées à une transition spécifique.
        Ces actions seraient implémentées dans le Moteur de Workflow (supervisor_logic, autonomous_logic).
        """
        logger.debug(f"Executing actions for transition {old_state} -> {new_state} via {event}")

        # Exemple d'actions (à implémenter dans les modules de logique du workflow)
        if event == "GENERATE_SUCCESS":
            # Action: Déclencher la tâche QC pour le bloc généré
            # workflow_tasks.run_qc_task.delay(self.block_id)
            logger.info(f"Action: Tâche QC déclenchée pour le bloc {self.block_id}")
        elif event == "QC_PASSED":
            if self.mode == "Autonome":
                # Action: Marquer le bloc comme validé, passer au suivant dans le plan
                # (La logique de passage au bloc suivant est dans autonomous_logic)
                logger.info(f"Action: Bloc {self.block_id} validé automatiquement.")
            # En mode Supervisé, l'action est de notifier le frontend pour validation utilisateur
            logger.info(f"Action: Bloc {self.block_id} prêt pour la prochaine étape.")
        elif event == "QC_FAILED":
            # Action: Déclencher le raffinement (automatique ou en attente de feedback utilisateur)
            # workflow_tasks.refine_content_block_task.delay(self.block_id, feedback=kwargs.get('qc_report'))
            logger.info(f"Action: Raffinement nécessaire pour le bloc {self.block_id}.")
        elif event == "USER_VALIDATE":
            # Action: Marquer le bloc comme validé par l'utilisateur
            logger.info(f"Action: Bloc {self.block_id} validé par l'utilisateur.")
        elif event == "USER_REDO":
            # Action: Déclencher le raffinement basé sur le feedback utilisateur
            # workflow_tasks.refine_content_block_task.delay(self.block_id, feedback=kwargs.get('user_feedback'))
            logger.info(f"Action: Raffinement déclenché par l'utilisateur pour le bloc {self.block_id}.")
        elif event == "REFINEMENT_SUCCESS":
            # Action: Le bloc raffiné est de nouveau soumis au QC
            # workflow_tasks.run_qc_task.delay(self.block_id)
            logger.info(f"Action: Bloc {self.block_id} raffiné, re-soumission au QC.")
        elif event in ["GENERATE_FAILED", "REFINEMENT_FAILED", "CRITICAL_FAIL"]:
            # Action: Gérer l'échec, potentiellement notifier l'utilisateur ou marquer le projet en erreur
            logger.error(f"Action: Échec critique détecté pour le bloc {self.block_id}.")
        
        # Note: Les actions réelles impliqueraient des appels aux services de persistance
        # pour mettre à jour l'état en base de données et des appels Celery pour les tâches asynchrones.
        # Ces appels seront gérés par les logiques de workflow (supervisor_logic.py, autonomous_logic.py)
        # qui utiliseront cette FSM.

    def get_current_state(self) -> str:
        """Retourne l'état actuel de la FSM."""
        return self.current_state

    def is_in_state(self, state: str) -> bool:
        """Vérifie si la FSM est dans un état donné."""
        return self.current_state == state

# Exemple d'utilisation (pour les tests ou la démonstration)
if __name__ == "__main__":
    # Simuler un bloc de contenu
    block_id_example = UUID("a1b2c3d4-e5f6-7890-1234-567890abcdef")
    project_id_example = UUID("12345678-1234-5678-1234-567812345678")

    # Mode Supervisé
    print("\n--- Simulation Mode Supervisé ---")
    fsm_supervised = ContentBlockStateMachine(
        initial_state="pending_generation", 
        mode="Supervisé", 
        block_id=block_id_example, 
        project_id=project_id_example
    )
    fsm_supervised.transition("GENERATE_STARTED")
    fsm_supervised.transition("GENERATE_SUCCESS") # -> qc_pending
    fsm_supervised.transition("QC_STARTED")
    fsm_supervised.transition("QC_PASSED") # -> pending_validation (spécifique au mode Supervisé)
    print(f"État actuel (Supervisé): {fsm_supervised.get_current_state()}")
    fsm_supervised.transition("USER_VALIDATE")
    print(f"État actuel (Supervisé): {fsm_supervised.get_current_state()}")

    # Tester un raffinement en mode Supervisé
    fsm_supervised_refine = ContentBlockStateMachine(
        initial_state="qc_passed", 
        mode="Supervisé", 
        block_id=UUID("b1b2c3d4-e5f6-7890-1234-567890abcdef"), 
        project_id=project_id_example
    )
    fsm_supervised_refine.transition("USER_REDO") # -> refinement_pending
    print(f"État actuel (Supervisé, après REDO): {fsm_supervised_refine.get_current_state()}")
    fsm_supervised_refine.transition("REFINEMENT_STARTED")
    fsm_supervised_refine.transition("REFINEMENT_SUCCESS") # -> qc_pending
    fsm_supervised_refine.transition("QC_STARTED")
    fsm_supervised_refine.transition("QC_FAILED") # -> refinement_pending (si QC échoue à nouveau)
    print(f"État actuel (Supervisé, après QC échoué de raffinement): {fsm_supervised_refine.get_current_state()}")


    # Mode Autonome
    print("\n--- Simulation Mode Autonome ---")
    fsm_autonomous = ContentBlockStateMachine(
        initial_state="pending_generation", 
        mode="Autonome", 
        block_id=UUID("c1b2c3d4-e5f6-7890-1234-567890abcdef"), 
        project_id=project_id_example
    )
    fsm_autonomous.transition("GENERATE_STARTED")
    fsm_autonomous.transition("GENERATE_SUCCESS") # -> qc_pending
    fsm_autonomous.transition("QC_STARTED")
    fsm_autonomous.transition("QC_PASSED") # -> validated (spécifique au mode Autonome)
    print(f"État actuel (Autonome): {fsm_autonomous.get_current_state()}")

    # Tester un échec QC en mode Autonome
    fsm_autonomous_fail = ContentBlockStateMachine(
        initial_state="qc_pending", 
        mode="Autonome", 
        block_id=UUID("d1b2c3d4-e5f6-7890-1234-567890abcdef"), 
        project_id=project_id_example
    )
    fsm_autonomous_fail.transition("QC_STARTED")
    fsm_autonomous_fail.transition("QC_FAILED") # -> refinement_pending (raffinement automatique)
    print(f"État actuel (Autonome, après QC échoué): {fsm_autonomous_fail.get_current_state()}")
    fsm_autonomous_fail.transition("REFINEMENT_STARTED")
    fsm_autonomous_fail.transition("REFINEMENT_FAILED") # -> refinement_failed
    print(f"État actuel (Autonome, après raffinement échoué): {fsm_autonomous_fail.get_current_state()}")

    # Tester une transition invalide
    print("\n--- Test Transition Invalide ---")
    try:
        fsm_invalid = ContentBlockStateMachine(
            initial_state="validated", 
            mode="Supervisé", 
            block_id=UUID("e1b2c3d4-e5f6-7890-1234-567890abcdef"), 
            project_id=project_id_example
        )
        fsm_invalid.transition("GENERATE_STARTED") # Ne devrait pas être possible
    except InvalidWorkflowStateException as e:
        print(f"Erreur attendue: {e.detail}")

