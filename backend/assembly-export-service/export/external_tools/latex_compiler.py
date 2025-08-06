# Fichier placeholder pour latex_compiler.py
# backend/assembly-export-service/export/external_tools/latex_compiler.py

import logging
import asyncio
import subprocess
import os
from typing import Dict, Any, Optional, List

from shared.config import get_settings
from shared.exceptions import ExternalToolError, InternalServerError

logger = logging.getLogger(__name__)
settings = get_settings()

class LatexCompilerClient:
    """
    Client pour le compilateur LaTeX (ex: pdflatex), encapsulant les appels à l'exécutable.
    Utilisé pour compiler des fichiers LaTeX en PDF.
    """
    def __init__(self, pdflatex_path: str):
        self.pdflatex_path = pdflatex_path # Chemin vers l'exécutable pdflatex
        logger.info(f"LatexCompilerClient initialisé avec l'exécutable à: {self.pdflatex_path}")

    async def check_availability(self) -> bool:
        """
        Vérifie si l'exécutable pdflatex est disponible.
        """
        try:
            process = await asyncio.create_subprocess_exec(
                self.pdflatex_path, "--version",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate(timeout=10) # Timeout de 10 secondes
            if process.returncode == 0:
                logger.info(f"pdflatex est disponible: {stdout.decode().splitlines()[0]}")
                return True
            else:
                logger.error(f"pdflatex --version a échoué avec le code {process.returncode}: {stderr.decode()}")
                return False
        except FileNotFoundError:
            logger.error(f"pdflatex executable not found at {self.pdflatex_path}.")
            return False
        except asyncio.TimeoutError:
            logger.warning(f"pdflatex --version a dépassé le temps imparti.")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la vérification de pdflatex: {e}", exc_info=True)
            return False

    async def compile_to_pdf(self, 
                             input_latex_path: str, 
                             output_pdf_path: str, 
                             working_dir: str, 
                             num_passes: int = 2, # Nombre de passes pour les références (souvent 2 ou 3)
                             timeout_per_pass: int = 60) -> Dict[str, Any]:
        """
        Compile un fichier LaTeX en PDF en utilisant pdflatex.
        Effectue plusieurs passes si nécessaire.
        Args:
            input_latex_path (str): Chemin vers le fichier LaTeX d'entrée.
            output_pdf_path (str): Chemin vers le fichier PDF de sortie.
            working_dir (str): Répertoire de travail pour la compilation (où les fichiers auxiliaires sont créés).
            num_passes (int): Nombre de passes de compilation à effectuer.
            timeout_per_pass (int): Délai d'expiration en secondes pour chaque passe de compilation.
        Returns:
            Dict[str, Any]: Résultat de la compilation (succès, message d'erreur, chemin de sortie).
        Raises:
            ExternalToolError: Si la compilation échoue ou si pdflatex n'est pas disponible.
        """
        if not await self.check_availability():
            raise ExternalToolError(tool_name="pdflatex", detail=f"pdflatex n'est pas disponible ou mal configuré à {self.pdflatex_path}.")

        # Le nom du fichier d'entrée sans le chemin, pour le passer à pdflatex
        latex_filename = os.path.basename(input_latex_path)

        # Commande de base pour pdflatex
        # -interaction=nonstopmode: ne s'arrête pas pour les erreurs
        # -output-directory: spécifie le répertoire de sortie pour tous les fichiers générés
        cmd = [
            self.pdflatex_path,
            "-interaction=nonstopmode",
            "-output-directory", working_dir,
            latex_filename # Le nom du fichier dans le répertoire de travail
        ]

        full_log_output = ""
        for i in range(num_passes):
            logger.info(f"Compilation LaTeX (Passe {i+1}/{num_passes}) pour {latex_filename}...")
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=working_dir # Exécuter la commande dans le répertoire de travail
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_per_pass)
                
                log_output = stdout.decode() + stderr.decode()
                full_log_output += f"\n--- Log Passe {i+1} ---\n" + log_output

                if process.returncode != 0:
                    logger.error(f"pdflatex failed on pass {i+1} with return code {process.returncode}. Output: {log_output}")
                    raise ExternalToolError(tool_name="pdflatex", detail=f"Erreur de compilation LaTeX (Passe {i+1}): {log_output}")
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                logger.warning(f"pdflatex pass {i+1} a dépassé le temps imparti ({timeout_per_pass}s).")
                raise ExternalToolError(tool_name="pdflatex", detail=f"Compilation LaTeX a dépassé le temps imparti sur la passe {i+1}.")
            except Exception as e:
                logger.error(f"Erreur inattendue lors de la compilation LaTeX (Passe {i+1}): {e}", exc_info=True)
                raise InternalServerError(detail=f"Erreur interne lors de la compilation LaTeX: {e}")

        final_pdf_path = os.path.join(working_dir, f"{os.path.splitext(latex_filename)[0]}.pdf")
        if not os.path.exists(final_pdf_path):
            raise ExternalToolError(tool_name="pdflatex", detail=f"Fichier PDF non généré à {final_pdf_path}. Vérifier les logs de compilation.")

        logger.info(f"Compilation LaTeX réussie. PDF généré à {final_pdf_path}")
        return {"success": True, "output_path": final_pdf_path, "message": "Compilation PDF réussie.", "log": full_log_output}

