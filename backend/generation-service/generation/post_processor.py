# backend/generation-service/generation/post_processor.py

import re
import logging
from typing import Dict, Any, List

from shared.exceptions import InternalServerError

logger = logging.getLogger(__name__)

class PostProcessor:
    """
    Effectue le nettoyage initial et le formatage de base sur le contenu extrait
    avant de le passer au Module QC.
    """
    def __init__(self):
        pass

    def clean_and_format_content(self, content_data: Dict[str, str], content_type: str) -> Dict[str, str]:
        """
        Nettoie et formate le contenu extrait des réponses LLM.
        Args:
            content_data (Dict[str, str]): Dictionnaire du contenu extrait (ex: {'Intuition': '...', 'Analogie': '...'}).
            content_type (str): Le type de contenu (ex: 'definition', 'intuition', 'exercise', 'text_block').
        Returns:
            Dict[str, str]: Le dictionnaire de contenu nettoyé et formaté.
        """
        cleaned_content_data = {}
        try:
            for key, value in content_data.items():
                if isinstance(value, str):
                    # Appliquer des règles de nettoyage génériques au texte
                    cleaned_value = self._apply_generic_cleaning(value)
                    
                    # Appliquer des règles spécifiques au LaTeX si le contenu est supposé être du LaTeX
                    if content_type in ['definition', 'intuition', 'proof_skeleton', 'text_block'] or key.endswith('_latex'):
                        cleaned_value = self._apply_latex_specific_cleaning(cleaned_value)
                    
                    cleaned_content_data[key] = cleaned_value
                else:
                    cleaned_content_data[key] = value # Conserver les non-chaînes telles quelles
            
            # Pour les exercices, s'assurer que les champs sont bien des chaînes
            if content_type == 'exercise':
                if 'prompt_latex' in cleaned_content_data and not isinstance(cleaned_content_data['prompt_latex'], str):
                    cleaned_content_data['prompt_latex'] = str(cleaned_content_data['prompt_latex'])
                if 'solution_latex' in cleaned_content_data and not isinstance(cleaned_content_data['solution_latex'], str):
                    cleaned_content_data['solution_latex'] = str(cleaned_content_data['solution_latex'])

            return cleaned_content_data
        except Exception as e:
            logger.error(f"Erreur inattendue lors du nettoyage/formatage du contenu de type '{content_type}': {e}", exc_info=True)
            raise InternalServerError(detail="Erreur interne lors du post-traitement du contenu LLM.")

    def _apply_generic_cleaning(self, text: str) -> str:
        """Applique des règles de nettoyage génériques au texte."""
        # Supprimer les espaces blancs excessifs au début/fin
        cleaned_text = text.strip()
        # Remplacer les multiples espaces par un seul espace
        cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)
        # Remplacer les multiples sauts de ligne par deux sauts de ligne (paragraphes)
        cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
        # Supprimer les phrases d'introduction/conclusion génériques du LLM
        cleaned_text = re.sub(r'^\s*(?:Voici la (?:définition|réponse|solution)|Contenu|Réponse):?\s*', '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE).strip()
        cleaned_text = re.sub(r'\s*(?:N\'hésitez pas si vous avez d\'autres questions|J\'espère que cela vous aide|Fin de la réponse)\s*\.?$', '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE).strip()
        
        return cleaned_text

    def _apply_latex_specific_cleaning(self, text: str) -> str:
        """Applique des règles de nettoyage spécifiques au LaTeX."""
        # Corriger les \$ en $ si le LLM les a échappés inutilement
        cleaned_text = text.replace(r'\$', '$')
        # S'assurer que les environnements mathématiques sont correctement délimités (simplifié)
        # Ceci est une vérification très basique, le QC fera une vérification plus robuste
        if '$' in cleaned_text and '$$' not in cleaned_text:
            # Si $ est présent mais pas $$, vérifier les paires non fermées
            # C'est complexe avec regex, souvent mieux géré par un parser dédié ou le QC
            pass 
        
        # Supprimer les \begin{document} et \end{document} si le LLM les a inclus
        cleaned_text = re.sub(r'\\begin\{document\}', '', cleaned_text)
        cleaned_text = re.sub(r'\\end\{document\}', '', cleaned_text)
        
        # Supprimer les \documentclass et \usepackage si le LLM les a inclus
        cleaned_text = re.sub(r'\\documentclass\{.*?\}', '', cleaned_text)
        cleaned_text = re.sub(r'\\usepackage\{.*?\}', '', cleaned_text)

        return cleaned_text

# Instancier le post-processeur
post_processor = PostProcessor()
