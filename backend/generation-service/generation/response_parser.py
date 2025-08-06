# Fichier placeholder pour response_parser.py
# backend/generation-service/generation/response_parser.py

import re
import json
import logging
from typing import Dict, Any, List, Optional

from shared.exceptions import BadRequestException, InternalServerError

logger = logging.getLogger(__name__)

class ResponseParser:
    """
    Contient la logique pour analyser les réponses brutes des LLMs,
    extraire le contenu structuré (texte, LaTeX, JSON) et gérer les variations de format.
    """
    def __init__(self):
        pass

    def parse_content_response(self, raw_text: str, content_type: str, expected_sections: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Parse la réponse brute d'un LLM en fonction du type de contenu attendu.
        Args:
            raw_text (str): La réponse texte brute du LLM.
            content_type (str): Le type de contenu attendu (ex: 'definition', 'intuition', 'exercise', 'text_block').
            expected_sections (Optional[List[str]]): Pour les blocs textuels, les noms de sections attendues (ex: ['Intuition', 'Analogie']).
        Returns:
            Dict[str, str]: Un dictionnaire où les clés sont les noms de section/champs et les valeurs sont le contenu extrait.
        Raises:
            BadRequestException: Si le format attendu n'est pas respecté.
            InternalServerError: Pour d'autres erreurs de parsing.
        """
        cleaned_text = raw_text.strip()
        
        if content_type in ['definition', 'intuition', 'proof_skeleton', 'text_block']:
            # Pour les contenus textuels avec ou sans sections
            return self._parse_sectioned_text(cleaned_text, expected_sections)
        elif content_type == 'exercise':
            # Pour les exercices qui devraient être au format JSON
            return self._parse_json_content(cleaned_text)
        else:
            logger.warning(f"Type de contenu '{content_type}' non géré par le parser. Retourne le texte brut.")
            return {"raw_content": cleaned_text}

    def _parse_sectioned_text(self, text: str, expected_sections: Optional[List[str]]) -> Dict[str, str]:
        """
        Parse un texte pour extraire des sections basées sur des marqueurs de titre (## Section).
        """
        extracted_content: Dict[str, str] = {}
        
        # Supprimer les marqueurs de code ``` qui peuvent encapsuler la réponse
        text = re.sub(r'^\s*```(?:[a-zA-Z0-9]+)?\s*$', '', text, flags=re.MULTILINE).strip()

        if not expected_sections:
            # Si aucune section spécifique n'est attendue, retourne le texte entier sous une clé par défaut
            return {"content": text}

        # Regex pour trouver les sections. Capture le nom de la section et le contenu.
        # Gère les variations de titres (#, ##, ###)
        # Le lookahead `(?=\n^\s*#+\s*\w+|\Z)` permet de capturer jusqu'au prochain titre ou la fin du texte
        section_pattern = re.compile(r'^\s*#+\s*(.+?)\s*$(.*?)(?=\n^\s*#+\s*\w+.*$|\Z)', re.MULTILINE | re.DOTALL)
        
        matches = list(section_pattern.finditer(text))

        if not matches:
            # Si aucun marqueur de section n'est trouvé mais des sections sont attendues,
            # on peut tenter de retourner le texte entier comme une section par défaut
            # ou lever une erreur si le format est strict.
            logger.warning(f"Aucun marqueur de section trouvé dans la réponse, sections attendues: {expected_sections}")
            # Pour l'instant, on retourne le texte entier comme "content" si une seule section est attendue
            if len(expected_sections) == 1:
                extracted_content[expected_sections[0]] = text
                return extracted_content
            raise BadRequestException(detail="Format de réponse inattendu: marqueurs de section manquants.")

        for match in matches:
            section_name_raw = match.group(1).strip()
            section_content_raw = match.group(2).strip()
            
            # Tente de faire correspondre le nom de section extrait avec les noms attendus (insensible à la casse)
            found_match = False
            for expected_name in expected_sections:
                if section_name_raw.lower() == expected_name.lower():
                    extracted_content[expected_name] = section_content_raw
                    found_match = True
                    break
            if not found_match:
                logger.warning(f"Section non attendue trouvée: '{section_name_raw}'. Ignorée.")
        
        # Vérifier si toutes les sections attendues ont été trouvées (si le format est strict)
        # if len(extracted_content) != len(expected_sections):
        #     logger.warning(f"Toutes les sections attendues n'ont pas été trouvées. Trouvé: {list(extracted_content.keys())}, Attendu: {expected_sections}")

        return extracted_content

    def _parse_json_content(self, text: str) -> Dict[str, Any]:
        """
        Parse un texte qui devrait contenir du JSON.
        Gère l'extraction du bloc JSON si le LLM l'a encapsulé dans des marqueurs de code.
        """
        # Cherche un bloc JSON encapsulé dans ```json ... ```
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            json_string = json_match.group(1).strip()
        else:
            # Si pas de marqueurs de code, suppose que le texte est directement du JSON
            json_string = text.strip()

        try:
            parsed_json = json.loads(json_string)
            return parsed_json
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de décodage JSON: {e}. Texte brut: {text[:200]}...")
            raise BadRequestException(detail=f"La réponse du LLM n'est pas un JSON valide: {e}")
        except Exception as e:
            logger.error(f"Erreur inattendue lors du parsing JSON: {e}", exc_info=True)
            raise InternalServerError(detail="Erreur interne lors du parsing de la réponse JSON.")

# Instancier le parser
response_parser = ResponseParser()
