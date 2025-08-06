# Fichier placeholder pour assembler.py
# backend/assembly-export-service/assembly/assembler.py

import logging
import httpx
from typing import Dict, Any, List, Optional
from uuid import UUID

from shared.config import get_settings
from shared.models import DocumentVersionResponse, ContentBlockResponse, ExerciseResponse, ProjectResponse
from shared.exceptions import InternalServerError, NotFoundException, BadRequestException, DocumentAssemblyError

logger = logging.getLogger(__name__)
settings = get_settings()

class DocumentAssembler:
    """
    Assemble les blocs de contenu validés d'une version de document pour former
    le document source final (LaTeX), prêt pour l'exportation.
    """
    def __init__(self, persistence_service_url: str):
        self.persistence_service_url = persistence_service_url
        logger.info("DocumentAssembler initialisé.")

    async def _get_document_data(self, document_version_id: UUID) -> Dict[str, Any]:
        """
        Récupère la version du document, sa structure, ses blocs de contenu et ses exercices
        depuis le service de persistance.
        """
        async with httpx.AsyncClient() as client:
            try:
                # 1. Récupérer la version du document
                version_resp = await client.get(f"{self.persistence_service_url}/internal/document-versions/{document_version_id}")
                version_resp.raise_for_status()
                document_version = DocumentVersionResponse(**version_resp.json())

                # 2. Récupérer le projet associé pour le style/niveau
                # Note: Dans notre modèle, document_id est aussi project_id pour simplifier
                project_resp = await client.get(f"{self.persistence_service_url}/internal/projects/{document_version.document_id}")
                project_resp.raise_for_status()
                project = ProjectResponse(**project_resp.json())

                # 3. Récupérer tous les blocs de contenu validés pour cette version
                blocks_resp = await client.get(f"{self.persistence_service_url}/internal/content-blocks", params={"version_id": str(document_version_id), "status": "validated"})
                blocks_resp.raise_for_status()
                content_blocks_data = {str(b['block_id']): ContentBlockResponse(**b) for b in blocks_resp.json()}

                # 4. Récupérer tous les exercices validés pour cette version
                exercises_resp = await client.get(f"{self.persistence_service_url}/internal/exercises", params={"version_id": str(document_version_id), "status": "validated"})
                exercises_resp.raise_for_status()
                exercises_data = {str(e['exercise_id']): ExerciseResponse(**e) for e in exercises_resp.json()}

                return {
                    "document_version": document_version,
                    "project": project,
                    "content_blocks": content_blocks_data,
                    "exercises": exercises_data
                }
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise NotFoundException(detail=f"Version de document {document_version_id} non trouvée ou données associées manquantes.")
                logger.error(f"Erreur HTTP lors de la récupération des données du document pour assemblage: {e.response.text}")
                raise InternalServerError(detail="Erreur du service de persistance lors de l'assemblage.")
            except httpx.RequestError as e:
                logger.error(f"Erreur réseau lors de la récupération des données du document pour assemblage: {e}")
                raise ServiceUnavailableException(detail="Le service de persistance n'est pas disponible.")
            except Exception as e:
                logger.error(f"Erreur inattendue lors de la récupération des données du document: {e}", exc_info=True)
                raise InternalServerError(detail=f"Erreur interne lors de la récupération des données du document: {e}")

    async def assemble_document(self, document_version_id: UUID) -> str:
        """
        Assemble le document final en LaTeX à partir des blocs de contenu validés.
        Args:
            document_version_id (UUID): L'ID de la version du document à assembler.
        Returns:
            str: Le contenu LaTeX complet du document assemblé.
        Raises:
            DocumentAssemblyError: Si l'assemblage échoue.
        """
        logger.info(f"Début de l'assemblage du document version {document_version_id}.")
        try:
            doc_data = await self._get_document_data(document_version_id)
            document_version = doc_data["document_version"]
            project = doc_data["project"]
            content_blocks = doc_data["content_blocks"]
            exercises = doc_data["exercises"]

            assembled_latex_parts: List[str] = []

            # 1. Ajouter le préambule LaTeX
            preamble = self._generate_latex_preamble(project.style, project.level)
            assembled_latex_parts.append(preamble)

            # 2. Ajouter les commandes de début de document
            assembled_latex_parts.append("\\begin{document}\n")
            assembled_latex_parts.append(f"\\title{{{project.title}}}\n")
            assembled_latex_parts.append(f"\\author{{Agent IA Mathématique}}\n")
            assembled_latex_parts.append("\\date{\\today}\n")
            assembled_latex_parts.append("\\maketitle\n")
            assembled_latex_parts.append("\\tableofcontents\n\n")

            # 3. Parcourir la structure du document et insérer le contenu des blocs
            # La structure est un dictionnaire JSONB dans document_versions.content_structure
            # Exemple de structure: {"chapters": [{"title": "...", "sections": [{"title": "...", "blocks": [{"block_id": "..."}]}]}]}
            
            if "chapters" in document_version.content_structure:
                for chapter_info in document_version.content_structure["chapters"]:
                    chapter_title = chapter_info.get("title", "Chapitre sans titre")
                    assembled_latex_parts.append(f"\\chapter{{{chapter_title}}}\n")
                    
                    if "sections" in chapter_info:
                        for section_info in chapter_info["sections"]:
                            section_title = section_info.get("title", "Section sans titre")
                            assembled_latex_parts.append(f"\\section{{{section_title}}}\n")
                            
                            if "blocks" in section_info:
                                for block_ref in section_info["blocks"]:
                                    block_id = block_ref.get("block_id")
                                    if block_id and str(block_id) in content_blocks:
                                        block = content_blocks[str(block_id)]
                                        assembled_latex_parts.append(f"% Block ID: {block.block_id}, Type: {block.block_type}\n")
                                        assembled_latex_parts.append(block.content_latex + "\n\n")
                                    else:
                                        logger.warning(f"Bloc de contenu {block_id} référencé dans la structure mais non trouvé ou non validé.")
                                        assembled_latex_parts.append(f"% [Contenu manquant pour le bloc {block_id}]\n\n")
            
            # 4. Gérer l'inclusion des exercices (ici, tous en annexe pour simplifier)
            if exercises:
                assembled_latex_parts.append("\\appendix\n")
                assembled_latex_parts.append("\\chapter*{Exercices}\n") # Chapitre sans numérotation
                assembled_latex_parts.append("\\addcontentsline{toc}{chapter}{Exercices}\n") # Ajouter à la table des matières
                assembled_latex_parts.append("\\section*{Liste des Exercices}\n")
                assembled_latex_parts.append("\\addcontentsline{toc}{section}{Liste des Exercices}\n")

                for ex_id, exercise in exercises.items():
                    assembled_latex_parts.append(f"\\subsection*{{Exercice {ex_id[:8]}}}\n")
                    assembled_latex_parts.append(exercise.prompt_latex + "\n\n")
                    if exercise.solution_latex:
                        assembled_latex_parts.append("\\textbf{Solution:}\n")
                        assembled_latex_parts.append(exercise.solution_latex + "\n\n")
            
            # 5. Ajouter les commandes de fin de document
            assembled_latex_parts.append("\\end{document}\n")

            full_latex_document = "".join(assembled_latex_parts)
            logger.info(f"Document version {document_version_id} assemblé avec succès (taille: {len(full_latex_document)} caractères).")
            return full_latex_document

        except Exception as e:
            logger.error(f"Erreur lors de l'assemblage du document version {document_version_id}: {e}", exc_info=True)
            raise DocumentAssemblyError(detail=f"Échec de l'assemblage du document: {e}")

    def _generate_latex_preamble(self, style: str, level: str) -> str:
        """
        Génère le préambule LaTeX en fonction du style et du niveau du projet.
        Ceci est une version simplifiée. En réalité, ce serait plus complexe.
        """
        preamble_parts = [
            "\\documentclass{book}\n",
            "\\usepackage[utf8]{inputenc}\n",
            "\\usepackage[T1]{fontenc}\n",
            "\\usepackage{amsmath}\n",
            "\\usepackage{amsfonts}\n",
            "\\usepackage{amssymb}\n",
            "\\usepackage{amsthm}\n",
            "\\usepackage{graphicx}\n",
            "\\usepackage{hyperref}\n",
            "\\hypersetup{colorlinks=true, linkcolor=blue, urlcolor=blue}\n",
            "\\usepackage{enumitem}\n", # Pour personnaliser les listes
            "\\usepackage{geometry}\n",
            "\\geometry{a4paper, margin=1in}\n",
            "\n"
        ]

        if style == "Bourbaki":
            preamble_parts.append("% Style Bourbaki: plus formel\n")
            preamble_parts.append("\\theoremstyle{definition}\n\\newtheorem{definition}{Définition}[chapter]\n")
            preamble_parts.append("\\theoremstyle{plain}\n\\newtheorem{theorem}{Théorème}[chapter]\n")
            preamble_parts.append("\\linespread{1.1}\\selectfont\n")
        elif style == "Feynman":
            preamble_parts.append("% Style Feynman: plus intuitif\n")
            preamble_parts.append("\\usepackage{ragged2e}\n\\justifying\n")
            preamble_parts.append("\\usepackage{xcolor}\n\\definecolor{feynmanblue}{HTML}{005A9C}\n")
            preamble_parts.append("\\usepackage{parskip}\n")
            preamble_parts.append("\\renewcommand{\\chapter}[1]{\\section*{#1}\\addcontentsline{toc}{chapter}{#1}}\n") # Pas de numérotation de chapitre
            preamble_parts.append("\\linespread{1.05}\\selectfont\n")
        elif style == "Hybride":
            preamble_parts.append("% Style Hybride\n")
            preamble_parts.append("\\theoremstyle{definition}\n\\newtheorem{definition}{Définition}[section]\n")
            preamble_parts.append("\\theoremstyle{plain}\n\\newtheorem{theorem}{Théorème}[section]\n")
            preamble_parts.append("\\linespread{1.1}\\selectfont\n")

        # Ajouter des packages ou des macros spécifiques au niveau si nécessaire
        if level in ["L1", "L2"]:
            preamble_parts.append("% Packages pour niveaux Licence\n")
        elif level in ["M1", "M2"]:
            preamble_parts.append("% Packages pour niveaux Master/Avancé\n")

        preamble_parts.append("\n")
        return "".join(preamble_parts)

