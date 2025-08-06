# Fichier placeholder pour sympy_client.py
# backend/qc-service/qc/external_tools/sympy_client.py

import logging
import sympy
from sympy.parsing.latex import parse_latex # Tente d'utiliser le parseur LaTeX de SymPy
from typing import Dict, Any, Optional

from shared.exceptions import ExternalToolError, BadRequestException, InternalServerError

logger = logging.getLogger(__name__)

class SymPyClient:
    """
    Client pour la bibliothèque SymPy, encapsulant les opérations de calcul symbolique.
    """
    def __init__(self):
        logger.info("SymPyClient initialisé.")

    async def parse_latex_expression(self, latex_expr: str) -> Any:
        """
        Parse une expression LaTeX en un objet SymPy.
        Utilise sympy.parsing.latex.parse_latex si disponible et suffisant.
        Args:
            latex_expr (str): L'expression mathématique en LaTeX.
        Returns:
            Any: L'objet SymPy représentant l'expression.
        Raises:
            BadRequestException: Si le parsing LaTeX échoue.
            ExternalToolError: Si SymPy n'est pas utilisable ou erreur interne.
        """
        try:
            # SymPy a un parseur LaTeX, mais il peut être limité pour des expressions complexes.
            # Il est souvent préférable de nettoyer le LaTeX avant de le passer à parse_latex.
            # Pour l'exemple, nous allons l'utiliser directement.
            parsed_expr = parse_latex(latex_expr)
            return parsed_expr
        except (sympy.parsing.latex.LaTeXParseError, SyntaxError) as e:
            logger.warning(f"SymPy LaTeX parsing error for '{latex_expr}': {e}")
            raise BadRequestException(detail=f"Erreur de parsing LaTeX pour SymPy: {e}")
        except Exception as e:
            logger.error(f"Erreur inattendue lors du parsing LaTeX vers SymPy: {e}", exc_info=True)
            raise ExternalToolError(tool_name="SymPy", detail=f"Erreur interne de parsing LaTeX: {e}")

    async def simplify_expression(self, latex_expr: str) -> Dict[str, Any]:
        """
        Simplifie une expression mathématique donnée en LaTeX et retourne le résultat.
        Args:
            latex_expr (str): L'expression mathématique en LaTeX.
        Returns:
            Dict[str, Any]: Dictionnaire contenant la version simplifiée en LaTeX et en chaîne.
        """
        try:
            sympy_expr = await self.parse_latex_expression(latex_expr)
            simplified_sympy_expr = sympy.simplify(sympy_expr)
            
            # Convertir l'expression SymPy simplifiée en LaTeX
            simplified_latex = sympy.latex(simplified_sympy_expr)
            
            return {
                "original_latex": latex_expr,
                "simplified_latex": simplified_latex,
                "simplified_str": str(simplified_sympy_expr)
            }
        except Exception as e:
            logger.error(f"Erreur lors de la simplification de l'expression '{latex_expr}': {e}", exc_info=True)
            raise ExternalToolError(tool_name="SymPy", detail=f"Échec de la simplification de l'expression: {e}")

    async def check_equality(self, latex_expr1: str, latex_expr2: str) -> bool:
        """
        Vérifie si deux expressions LaTeX sont égales symboliquement.
        Args:
            latex_expr1 (str): La première expression en LaTeX.
            latex_expr2 (str): La deuxième expression en LaTeX.
        Returns:
            bool: True si les expressions sont égales, False sinon.
        """
        try:
            expr1_sympy = await self.parse_latex_expression(latex_expr1)
            expr2_sympy = await self.parse_latex_expression(latex_expr2)
            
            # Vérifie si la différence entre les deux expressions simplifie à zéro
            return sympy.simplify(expr1_sympy - expr2_sympy) == 0
        except Exception as e:
            logger.error(f"Erreur lors de la vérification d'égalité entre '{latex_expr1}' et '{latex_expr2}': {e}", exc_info=True)
            raise ExternalToolError(tool_name="SymPy", detail=f"Échec de la vérification d'égalité: {e}")

# Instancier le client SymPy
sympy_client = SymPyClient()

