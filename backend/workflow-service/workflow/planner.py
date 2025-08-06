# backend/workflow-service/workflow/planner.py

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

from shared.models import ProjectResponse, ContentBlockResponse, DocumentVersionResponse

logger = logging.getLogger(__name__)

class AutonomousPlanner:
    """
    Implémente les algorithmes de planification pour le Mode Autonome du Moteur de Workflow.
    Détermine la séquence des tâches (chapitres, sections, blocs) à traiter.
    """
    def __init__(self):
        pass

    def generate_initial_plan(self, document_structure: Dict[str, Any], project_id: UUID, document_version_id: UUID) -> List[Dict[str, Any]]:
        """
        Génère un plan d'exécution initial pour un document en mode Autonome.
        Le plan est une liste ordonnée de "tâches" ou "étapes" à exécuter.
        Pour une première version, ce sera un parcours simple de l'arborescence du document.

        Args:
            document_structure (Dict[str, Any]): La structure arborescente du document (chapitres, sections, blocs).
            project_id (UUID): L'ID du projet.
            document_version_id (UUID): L'ID de la version du document.

        Returns:
            List[Dict[str, Any]]: Une liste d'étapes de plan. Chaque étape peut contenir
                                   des informations sur le bloc à générer, son type, etc.
        """
        plan = []
        logger.info(f"Génération du plan initial pour le document version {document_version_id} du projet {project_id}")

        # Exemple de structure de document:
        # {
        #   "chapters": [
        #     {"chapter_id": "chap1", "title": "Chapitre 1", "sections": [
        #       {"section_id": "sec1.1", "title": "Section 1.1", "blocks": [
        #         {"block_id": "block1.1.1", "block_type": "definition"},
        #         {"block_id": "block1.1.2", "block_type": "intuition"}
        #       ]}
        #     ]}
        #   ]
        # }

        # Parcours simple de la structure pour créer des étapes de génération de blocs
        if "chapters" in document_structure:
            for chapter in document_structure["chapters"]:
                # Ajouter une étape de "point de contrôle" pour le début du chapitre
                plan.append({
                    "type": "checkpoint",
                    "checkpoint_type": "chapter_start",
                    "chapter_id": chapter.get("chapter_id"),
                    "title": chapter.get("title")
                })
                if "sections" in chapter:
                    for section in chapter["sections"]:
                        if "blocks" in section:
                            for block_info in section["blocks"]:
                                plan.append({
                                    "type": "generate_block",
                                    "block_id": block_info.get("block_id"),
                                    "block_type": block_info.get("block_type"),
                                    "section_id": section.get("section_id"),
                                    "chapter_id": chapter.get("chapter_id")
                                })
        
        # Ajouter une étape finale d'assemblage/exportation
        plan.append({
            "type": "final_assembly",
            "document_version_id": str(document_version_id)
        })

        logger.info(f"Plan initial généré avec {len(plan)} étapes.")
        return plan

    async def get_next_task_in_plan(self, project: ProjectResponse, document_version: DocumentVersionResponse, current_plan_index: int, all_content_blocks: List[ContentBlockResponse]) -> Optional[Dict[str, Any]]:
        """
        Détermine la prochaine tâche à exécuter dans le plan autonome.
        Args:
            project (ProjectResponse): L'objet projet actuel.
            document_version (DocumentVersionResponse): La version actuelle du document.
            current_plan_index (int): L'index actuel dans le plan d'exécution du projet.
            all_content_blocks (List[ContentBlockResponse]): Tous les blocs de contenu de la version actuelle.
        Returns:
            Optional[Dict[str, Any]]: La prochaine étape du plan, ou None si le plan est terminé.
        """
        # Dans un système réel, le plan serait stocké dans la DB du projet
        # et mis à jour. Ici, nous le générons à la volée pour l'exemple.
        plan = self.generate_initial_plan(document_version.content_structure, project.project_id, document_version.version_id)

        if current_plan_index >= len(plan):
            return None # Le plan est terminé

        next_step = plan[current_plan_index]

        # Logique pour sauter les étapes déjà traitées (si le plan est persistant)
        # Par exemple, si l'étape est 'generate_block' et le bloc correspondant est déjà 'validated'
        if next_step.get("type") == "generate_block":
            block_id_in_plan = next_step.get("block_id")
            # Trouver le bloc correspondant dans la liste des blocs actuels
            current_block = next((b for b in all_content_blocks if str(b.block_id) == block_id_in_plan), None)
            if current_block and current_block.status in ["validated", "generation_failed", "refinement_failed", "archived"]:
                logger.info(f"Bloc {block_id_in_plan} déjà traité ({current_block.status}), saut de l'étape.")
                return await self.get_next_task_in_plan(project, document_version, current_plan_index + 1, all_content_blocks)
        
        logger.info(f"Prochaine étape du plan pour le projet {project.project_id}: {next_step}")
        return next_step

# Instancier le planificateur
autonomous_planner = AutonomousPlanner()
