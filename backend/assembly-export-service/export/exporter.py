# Fichier placeholder pour exporter.py
# backend/assembly-export-service/export/exporter.py

import logging
import asyncio
import subprocess
import os
from typing import Dict, Any, List, Optional
from uuid import UUID

from shared.config import get_settings
from shared.exceptions import ExternalToolError, InternalServerError, DocumentExportError

logger = logging.getLogger(__name__)
settings = get_settings()

class DocumentExporter:
    """
    Gère l'exportation des documents assemblés dans divers formats (PDF, LaTeX, Markdown).
    S'appuie sur des outils externes comme Pandoc et un compilateur LaTeX.
    """
    def __init__(self, pandoc_path: str, pdflatex_path: str):
        self.pandoc_path = pandoc_path
        self.pdflatex_path = pdflatex_path
        logger.info(f"DocumentExporter initialisé. Pandoc: {self.pandoc_path}, pdflatex: {self.pdflatex_path}")

    async def check_tool_availability(self):
        """
        Vérifie si les exécutables des outils externes sont disponibles.
        """
        try:
            await asyncio.create_subprocess_exec(self.pandoc_path, "--version", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"Pandoc disponible à {self.pandoc_path}")
        except FileNotFoundError:
            raise ExternalToolError(tool_name="Pandoc", detail=f"Pandoc executable not found at {self.pandoc_path}.")
        except Exception as e:
            raise ExternalToolError(tool_name="Pandoc", detail=f"Erreur lors de la vérification de Pandoc: {e}")

        try:
            await asyncio.create_subprocess_exec(self.pdflatex_path, "--version", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"pdflatex disponible à {self.pdflatex_path}")
        except FileNotFoundError:
            raise ExternalToolError(tool_name="pdflatex", detail=f"pdflatex executable not found at {self.pdflatex_path}.")
        except Exception as e:
            raise ExternalToolError(tool_name="pdflatex", detail=f"Erreur lors de la vérification de pdflatex: {e}")
        
        logger.info("Tous les outils d'exportation externes sont disponibles.")

    async def export_document(self, document_latex_content: str, document_version_id: UUID, formats: List[str]) -> List[Dict[str, str]]:
        """
        Exporte le document LaTeX assemblé dans les formats spécifiés.
        Args:
            document_latex_content (str): Le contenu LaTeX complet du document assemblé.
            document_version_id (UUID): L'ID de la version du document.
            formats (List[str]): Liste des formats d'exportation souhaités (ex: ['pdf', 'latex_source', 'markdown']).
        Returns:
            List[Dict[str, str]]: Liste de dictionnaires avec le format et l'URL/chemin du fichier exporté.
        Raises:
            DocumentExportError: Si l'exportation échoue pour un format critique.
        """
        exported_files: List[Dict[str, str]] = []
        temp_dir = f"/tmp/exports/{document_version_id}" # Répertoire temporaire pour les fichiers
        os.makedirs(temp_dir, exist_ok=True)
        
        base_filename = f"document_{document_version_id}"
        latex_input_path = os.path.join(temp_dir, f"{base_filename}.tex")

        try:
            # Écrire le contenu LaTeX dans un fichier temporaire
            with open(latex_input_path, "w", encoding="utf-8") as f:
                f.write(document_latex_content)
            logger.info(f"Contenu LaTeX écrit dans {latex_input_path}")

            for fmt in formats:
                output_path = os.path.join(temp_dir, f"{base_filename}.{fmt}")
                success = False
                error_message = None

                if fmt == "latex_source":
                    # Pour le LaTeX source, il suffit de copier le fichier d'entrée
                    output_path = os.path.join(temp_dir, f"{base_filename}.tex") # S'assurer que l'extension est .tex
                    # Le fichier est déjà écrit, donc on peut juste le référencer
                    success = True
                    logger.info(f"Exportation LaTeX source pour {document_version_id} réussie.")
                elif fmt == "pdf":
                    success, error_message = await self._export_to_pdf(latex_input_path, output_path, temp_dir)
                    logger.info(f"Exportation PDF pour {document_version_id}: {'Réussie' if success else 'Échouée'}")
                elif fmt == "markdown":
                    success, error_message = await self._export_with_pandoc(latex_input_path, output_path, "markdown")
                    logger.info(f"Exportation Markdown pour {document_version_id}: {'Réussie' if success else 'Échouée'}")
                elif fmt == "html":
                    success, error_message = await self._export_with_pandoc(latex_input_path, output_path, "html")
                    logger.info(f"Exportation HTML pour {document_version_id}: {'Réussie' if success else 'Échouée'}")
                # Ajoutez d'autres formats ici

                if success:
                    # Dans un système réel, vous téléverseriez ce fichier vers un stockage cloud (S3, GCS)
                    # et retourneriez son URL publique ou signée.
                    # Pour cet exemple, nous retournons le chemin local temporaire.
                    download_url = f"/downloads/{document_version_id}/{base_filename}.{fmt}" # URL conceptuelle de téléchargement
                    exported_files.append({"format": fmt, "url": download_url})
                else:
                    exported_files.append({"format": fmt, "url": None, "error": error_message})
                    logger.error(f"Échec de l'exportation pour le format {fmt}: {error_message}")
                    # Si l'exportation PDF est critique, on pourrait lever une exception ici
                    # raise DocumentExportError(detail=f"Échec de l'exportation PDF: {error_message}")

            return exported_files

        except Exception as e:
            logger.error(f"Erreur critique lors de l'exportation du document {document_version_id}: {e}", exc_info=True)
            raise DocumentExportError(detail=f"Échec critique de l'exportation du document: {e}")
        finally:
            # Nettoyer les fichiers temporaires après l'exportation
            # shutil.rmtree(temp_dir, ignore_errors=True)
            logger.info(f"Nettoyage des fichiers temporaires dans {temp_dir} (non implémenté pour l'exemple).")

    async def _export_to_pdf(self, input_latex_path: str, output_pdf_path: str, working_dir: str) -> tuple[bool, Optional[str]]:
        """
        Compile un fichier LaTeX en PDF en utilisant pdflatex.
        Effectue plusieurs passes pour les références et la table des matières.
        """
        # Utiliser latexmk ou appeler pdflatex plusieurs fois
        # Pour simplifier, nous allons appeler pdflatex deux fois.
        commands = [
            [self.pdflatex_path, "-interaction=nonstopmode", "-output-directory", working_dir, input_latex_path],
            [self.pdflatex_path, "-interaction=nonstopmode", "-output-directory", working_dir, input_latex_path] # Deuxième passe pour les références
        ]
        
        full_output = ""
        for cmd in commands:
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=working_dir # Exécuter la commande dans le répertoire de travail
                )
                stdout, stderr = await process.communicate(timeout=120) # Timeout de 2 minutes
                full_output += stdout.decode() + stderr.decode()

                if process.returncode != 0:
                    logger.error(f"pdflatex failed with return code {process.returncode}. Output: {full_output}")
                    return False, f"Erreur de compilation LaTeX: {full_output}"
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return False, "Compilation PDF a dépassé le temps imparti."
            except FileNotFoundError:
                return False, f"pdflatex executable not found at {self.pdflatex_path}."
            except Exception as e:
                return False, f"Erreur inattendue lors de la compilation PDF: {e}"

        if not os.path.exists(output_pdf_path):
            return False, f"Fichier PDF non généré à {output_pdf_path}. Vérifier les logs LaTeX."
        
        return True, None

    async def _export_with_pandoc(self, input_latex_path: str, output_path: str, target_format: str) -> tuple[bool, Optional[str]]:
        """
        Convertit un fichier LaTeX vers un autre format en utilisant Pandoc.
        """
        # Exemple: convertir LaTeX en Markdown avec rendu MathJax
        cmd = [
            self.pandoc_path,
            input_latex_path,
            "-o", output_path,
            "--to", target_format,
            "--mathml", # Ou --mathjax pour le rendu mathématique
            # Ajoutez d'autres options Pandoc si nécessaire (ex: --standalone pour HTML complet)
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate(timeout=60) # Timeout de 1 minute

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"Pandoc failed for {target_format} with return code {process.returncode}: {error_msg}")
                return False, f"Erreur de conversion Pandoc: {error_msg}"
            
            if not os.path.exists(output_path):
                return False, f"Fichier {target_format} non généré à {output_path}."

            return True, None
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return False, f"Conversion {target_format} a dépassé le temps imparti."
        except FileNotFoundError:
            return False, f"Pandoc executable not found at {self.pandoc_path}."
        except Exception as e:
            return False, f"Erreur inattendue lors de la conversion Pandoc vers {target_format}: {e}"

