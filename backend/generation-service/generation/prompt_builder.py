# Fichier placeholder pour prompt_builder.py
# backend/generation-service/generation/prompt_builder.py

import logging
import httpx
import yaml
import os
from typing import Dict, Any, List, Optional
from uuid import UUID

from shared.config import get_settings
from shared.exceptions import InternalServerError, BadRequestException, ServiceUnavailableException

logger = logging.getLogger(__name__)
settings = get_settings()

class PromptBuilder:
    """
    Construit dynamiquement les prompts envoyés aux LLMs,
    en intégrant le contexte et les données de la Base de Connaissances (KB).
    """
    def __init__(self, kb_service_url: str):
        self.kb_service_url = kb_service_url
        self.prompt_templates: Dict[str, Any] = self._load_prompt_templates()
        logger.info("PromptBuilder initialisé et templates chargés.")

    def _load_prompt_templates(self) -> Dict[str, Any]:
        """
        Charge les templates de prompts depuis le fichier YAML.
        """
        # Chemin vers le fichier templates.yaml (supposé être dans le répertoire docs/prompts)
        # En production, ce fichier pourrait être monté via un ConfigMap Kubernetes
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../docs/prompts/templates.yaml")
        if not os.path.exists(template_path):
            logger.error(f"Fichier de templates de prompts non trouvé: {template_path}")
            raise FileNotFoundError(f"Fichier de templates de prompts manquant: {template_path}")
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                templates = yaml.safe_load(f)
            return {t['type']: t for t in templates.get('prompts', [])}
        except yaml.YAMLError as e:
            logger.error(f"Erreur de parsing YAML pour les templates de prompts: {e}")
            raise InternalServerError(detail="Erreur de configuration des templates de prompts.")
        except Exception as e:
            logger.error(f"Erreur inattendue lors du chargement des templates de prompts: {e}", exc_info=True)
            raise InternalServerError(detail="Échec du chargement des templates de prompts.")

    async def _get_kb_data(self, concept_id: Optional[UUID], theorem_id: Optional[UUID], level: str, style: str) -> Dict[str, Any]:
        """
        Récupère les données pertinentes de la KB pour enrichir le prompt.
        """
        kb_data = {}
        async with httpx.AsyncClient() as client:
            try:
                if concept_id:
                    # Obtenir le concept lui-même
                    resp = await client.get(f"{self.kb_service_url}/internal/concepts/{concept_id}")
                    resp.raise_for_status()
                    kb_data["concept"] = resp.json()

                    # Obtenir les définitions formelles et intuitives
                    resp_defs_formel = await client.get(f"{self.kb_service_url}/internal/concepts/{concept_id}/definitions", params={"type": "formelle", "level": level})
                    resp_defs_formel.raise_for_status()
                    kb_data["formal_definitions"] = resp_defs_formel.json()

                    resp_defs_intuitive = await client.get(f"{self.kb_service_url}/internal/concepts/{concept_id}/definitions", params={"type": "intuitive", "level": level})
                    resp_defs_intuitive.raise_for_status()
                    kb_data["intuitive_definitions"] = resp_defs_intuitive.json()

                    # Obtenir les prérequis
                    resp_prereqs = await client.get(f"{self.kb_service_url}/internal/concepts/{concept_id}/prerequisites", params={"recursive": True})
                    resp_prereqs.raise_for_status()
                    kb_data["prerequisite_concepts"] = resp_prereqs.json()

                    # Obtenir les pièges pédagogiques
                    resp_pitfalls = await client.get(f"{self.kb_service_url}/internal/concepts/{concept_id}/pitfalls", params={"level": level})
                    resp_pitfalls.raise_for_status()
                    kb_data["pitfalls"] = resp_pitfalls.json()

                    # Obtenir les analogies
                    resp_analogies = await client.get(f"{self.kb_service_url}/internal/concepts/{concept_id}/analogies", params={"level": level})
                    resp_analogies.raise_for_status()
                    kb_data["analogies"] = resp_analogies.json()
                
                if theorem_id:
                    # Obtenir le théorème lui-même
                    resp = await client.get(f"{self.kb_service_url}/internal/theorems/{theorem_id}")
                    resp.raise_for_status()
                    kb_data["theorem"] = resp.json()

            except httpx.HTTPStatusError as e:
                logger.warning(f"KB Service returned HTTP error during data retrieval: {e.request.url} - {e.response.text}")
                # Ne pas lever d'exception, le prompt builder peut fonctionner avec des données KB partielles
            except httpx.RequestError as e:
                logger.error(f"Network error calling KB Service: {e.request.url} - {e}")
                raise ServiceUnavailableException(detail="Le KB Service n'est pas disponible pour construire le prompt.")
        return kb_data

    async def build_prompt(self, 
                           content_type: str, 
                           level: str, 
                           style: str, 
                           context_data: Dict[str, Any], 
                           concept_id: Optional[UUID] = None, 
                           theorem_id: Optional[UUID] = None) -> str:
        """
        Construit le prompt final pour le LLM.
        Args:
            content_type (str): Type de contenu à générer (ex: 'definition', 'intuition').
            level (str): Niveau pédagogique cible.
            style (str): Style rédactionnel.
            context_data (Dict[str, Any]): Données de contexte supplémentaires (ex: texte précédent, feedback pour raffinement).
            concept_id (Optional[UUID]): ID du concept mathématique pertinent.
            theorem_id (Optional[UUID]): ID du théorème pertinent.
        Returns:
            str: Le prompt final formaté.
        Raises:
            BadRequestException: Si le template de prompt est introuvable.
            InternalServerError: Pour d'autres erreurs.
        """
        template_info = self.prompt_templates.get(content_type)
        if not template_info:
            raise BadRequestException(detail=f"Aucun template de prompt trouvé pour le type de contenu: {content_type}")

        selected_template = None
        # Chercher le template le plus spécifique (style, puis niveau)
        for template in template_info.get('templates', []):
            if template.get('style') == style and (template.get('level') == level or template.get('level') == 'default'):
                selected_template = template
                break
            elif template.get('style') == 'default' and (template.get('level') == level or template.get('level') == 'default'):
                selected_template = template # Fallback au template par défaut si pas de match exact de style

        if not selected_template:
            # Si aucun template spécifique n'est trouvé, utiliser le template par défaut du type
            for template in template_info.get('templates', []):
                if template.get('style') == template_info.get('default_style') and template.get('level') == 'default':
                    selected_template = template
                    break
            if not selected_template:
                raise InternalServerError(detail=f"Aucun template par défaut trouvé pour le type de contenu: {content_type}")

        template_string = selected_template['content']
        
        # Récupérer les données de la KB
        kb_data = await self._get_kb_data(concept_id, theorem_id, level, style)

        # Préparer les placeholders pour le formatage du template
        placeholders = {
            "level": level,
            "style": style,
            "concept_name": kb_data.get("concept", {}).get("name", "le concept"),
            "formal_definition_from_KB": kb_data.get("formal_definitions", [{}])[0].get("content_latex", "aucune définition formelle disponible") if kb_data.get("formal_definitions") else "aucune définition formelle disponible",
            "intuitive_definition_from_KB": kb_data.get("intuitive_definitions", [{}])[0].get("content_latex", "aucune définition intuitive disponible") if kb_data.get("intuitive_definitions") else "aucune définition intuitive disponible",
            "prerequisite_concepts_names": ", ".join([p.get("name") for p in kb_data.get("prerequisite_concepts", [])]) or "les concepts de base",
            "verified_analogy_from_KB": kb_data.get("analogies", [{}])[0].get("description_latex", "aucune analogie vérifiée") if kb_data.get("analogies") else "aucune analogie vérifiée",
            "pitfall_description_from_KB": kb_data.get("pitfalls", [{}])[0].get("description_short", "aucun piège courant connu") if kb_data.get("pitfalls") else "aucun piège courant connu",
            "theorem_name": kb_data.get("theorem", {}).get("name", "le théorème"),
            "theorem_statement_from_KB": kb_data.get("theorem", {}).get("statement_latex", "aucun énoncé de théorème disponible"),
            "proof_ideas_from_KB": "Idées de preuve: " + ", ".join([p.get("description_latex") for p in kb_data.get("theorem", {}).get("proof_sketches", [])]) if kb_data.get("theorem") else "aucune idée de preuve disponible",
            "related_concepts_names": ", ".join([c.get("name") for c in kb_data.get("related_concepts", [])]) or "concepts connexes", # À implémenter dans _get_kb_data si besoin
            "block_type": content_type, # Pour les templates génériques de text_block
            "main_concept_name": kb_data.get("concept", {}).get("name", "le sujet"),
        }
        
        # Ajouter les données de contexte spécifiques à la tâche
        placeholders.update(context_data)

        try:
            # Remplir le template avec les placeholders
            final_prompt = template_string.format(**placeholders)
            return final_prompt
        except KeyError as e:
            logger.error(f"Placeholder manquant dans le template de prompt pour le type '{content_type}': {e}. Template: {template_string}", exc_info=True)
            raise InternalServerError(detail=f"Erreur de construction du prompt: un placeholder est manquant dans le template. Veuillez vérifier le template pour {content_type}.")
        except Exception as e:
            logger.error(f"Erreur inattendue lors du formatage du prompt: {e}", exc_info=True)
            raise InternalServerError(detail=f"Erreur interne lors de la construction du prompt: {e}")

# Instancier le PromptBuilder (sera initialisé dans main.py)
# prompt_builder = PromptBuilder(kb_service_url=settings.KB_SERVICE_URL)
