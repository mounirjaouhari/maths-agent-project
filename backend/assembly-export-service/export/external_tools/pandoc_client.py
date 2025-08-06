# Fichier placeholder pour pandoc_client.py
# backend/assembly-export-service/export/external_tools/pandoc_client.py

import logging
import asyncio
import subprocess
import os
from typing import Dict, Any, Optional, List

from shared.config import get_settings
from shared.exceptions import ExternalToolError, InternalServerError, BadRequestException

logger = logging.getLogger(__name__)
settings = get_settings()

class PandocClient:
    """
    Client pour l'outil en ligne de commande Pandoc, encapsulant les appels à l'exécutable Pandoc.
    Utilisé pour convertir des documents entre différents formats.
    """
    def __init__(self, pandoc_path: str):
        self.pandoc_path = pandoc_path # Chemin vers l'exécutable Pandoc
        logger.info(f"PandocClient initialisé avec l'exécutable à: {self.pandoc_path}")

    async def check_availability(self) -> bool:
        """
        Vérifie si l'exécutable Pandoc est disponible.
        """
        try:
            process = await asyncio.create_subprocess_exec(
                self.pandoc_path, "--version",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate(timeout=10) # Timeout de 10 secondes
            if process.returncode == 0:
                logger.info(f"Pandoc est disponible: {stdout.decode().splitlines()[0]}")
                return True
            else:
                logger.error(f"Pandoc --version a échoué avec le code {process.returncode}: {stderr.decode()}")
                return False
        except FileNotFoundError:
            logger.error(f"Pandoc executable not found at {self.pandoc_path}.")
            return False
        except asyncio.TimeoutError:
            logger.warning(f"Pandoc --version a dépassé le temps imparti.")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la vérification de Pandoc: {e}", exc_info=True)
            return False

    async def convert(self, 
                      input_path: str, 
                      output_path: str, 
                      from_format: str, 
                      to_format: str, 
                      options: Optional[List[str]] = None,
                      timeout: int = 120) -> Dict[str, Any]:
        """
        Convertit un fichier d'un format à un autre en utilisant Pandoc.
        Args:
            input_path (str): Chemin vers le fichier d'entrée.
            output_path (str): Chemin vers le fichier de sortie.
            from_format (str): Format du fichier d'entrée (ex: 'latex').
            to_format (str): Format du fichier de sortie (ex: 'markdown', 'html', 'pdf').
            options (Optional[List[str]]): Options supplémentaires à passer à Pandoc (ex: ['--mathjax']).
            timeout (int): Délai d'expiration en secondes pour l'exécution de Pandoc.
        Returns:
            Dict[str, Any]: Résultat de la conversion (succès, message d'erreur, chemin de sortie).
        Raises:
            ExternalToolError: Si la conversion échoue ou si Pandoc n'est pas disponible.
        """
        if not await self.check_availability():
            raise ExternalToolError(tool_name="Pandoc", detail=f"Pandoc n'est pas disponible ou mal configuré à {self.pandoc_path}.")

        cmd = [
            self.pandoc_path,
            "--from", from_format,
            "--to", to_format,
            input_path,
            "-o", output_path
        ]
        if options:
            cmd.extend(options)

        logger.info(f"Exécution de Pandoc: {' '.join(cmd)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"Pandoc conversion failed with code {process.returncode}: {error_msg}")
                raise ExternalToolError(tool_name="Pandoc", detail=f"Échec de la conversion Pandoc: {error_msg}")

            if not os.path.exists(output_path):
                raise ExternalToolError(tool_name="Pandoc", detail=f"Fichier de sortie non généré à {output_path}.")

            logger.info(f"Conversion Pandoc réussie de {from_format} vers {to_format}.")
            return {"success": True, "output_path": output_path, "message": "Conversion réussie."}

        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            logger.warning(f"Pandoc conversion de {from_format} vers {to_format} a dépassé le temps imparti ({timeout}s).")
            raise ExternalToolError(tool_name="Pandoc", detail=f"Conversion Pandoc a dépassé le temps imparti.")
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la conversion Pandoc: {e}", exc_info=True)
            raise InternalServerError(detail=f"Erreur interne lors de la conversion Pandoc: {e}")

