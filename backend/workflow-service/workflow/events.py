# backend/workflow-service/workflow/events.py

# Définition des événements qui peuvent déclencher des transitions d'états
# Ces constantes sont utilisées par la ContentBlockStateMachine et les logiques de workflow.

class EVENTS:
    """
    Définit les types d'événements qui peuvent déclencher des transitions
    dans les Machines à États Finis du Workflow.
    """
    # Événements liés à la Génération
    GENERATE_STARTED = "GENERATE_STARTED"
    GENERATE_SUCCESS = "GENERATE_SUCCESS"
    GENERATE_FAILED = "GENERATE_FAILED"

    # Événements liés au Contrôle Qualité (QC)
    QC_STARTED = "QC_STARTED"
    QC_PASSED = "QC_PASSED"
    QC_FAILED = "QC_FAILED"

    # Événements liés au Raffinement
    REFINEMENT_NEEDED = "REFINEMENT_NEEDED" # Déclenché par QC_FAILED ou USER_REDO
    REFINEMENT_STARTED = "REFINEMENT_STARTED"
    REFINEMENT_SUCCESS = "REFINEMENT_SUCCESS"
    REFINEMENT_FAILED = "REFINEMENT_FAILED"

    # Événements liés à l'Interaction Utilisateur (Mode Supervisé)
    USER_VALIDATE = "USER_VALIDATE" # L'utilisateur valide le contenu
    USER_REDO = "USER_REDO" # L'utilisateur demande un raffinement
    USER_SIGNAL_ADD_ELEMENT = "USER_SIGNAL_ADD_ELEMENT" # L'utilisateur demande d'ajouter un élément (ex: concept)
    USER_SIGNAL_QC_OK = "USER_SIGNAL_QC_OK" # L'utilisateur valide le rapport QC
    USER_SIGNAL_PROBLEM_DETECTED = "USER_SIGNAL_PROBLEM_DETECTED" # L'utilisateur signale un problème après QC
    USER_SIGNAL_ALL_APPROVED = "USER_SIGNAL_ALL_APPROVED" # L'utilisateur approuve le document final

    # Événements liés à l'Assemblage et l'Exportation
    ASSEMBLY_COMPLETED = "ASSEMBLY_COMPLETED"
    EXPORT_COMPLETED = "EXPORT_COMPLETED"
    EXPORT_FAILED = "EXPORT_FAILED"

    # Événements de gestion interne / erreurs critiques
    ARCHIVE = "ARCHIVE" # Pour archiver un bloc (ex: nouvelle version créée)
    CRITICAL_FAIL = "CRITICAL_FAIL" # Erreur non récupérable

    # Événements de planification autonome (si le planificateur est plus sophistiqué)
    INTERNAL_PLAN_STEP_COMPLETED = "INTERNAL_PLAN_STEP_COMPLETED"
    QC_THRESHOLD_NOT_MET = "QC_THRESHOLD_NOT_MET" # Le score QC n'atteint pas le seuil en mode autonome
    REFINEMENT_ATTEMPTS_EXHAUSTED = "REFINEMENT_ATTEMPTS_EXHAUSTED" # Max tentatives de raffinement atteintes
    MAJOR_CHECKPOINT_REACHED = "MAJOR_CHECKPOINT_REACHED" # Point de contrôle majeur atteint dans le plan autonome
