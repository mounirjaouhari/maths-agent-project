# Fichier placeholder pour refinement_engine.py
# backend/interaction-service/refinement/refinement_engine.py

import logging
import httpx
from typing import Dict, Any, Optional
from uuid import UUID

from shared.config import get_settings
from shared.exceptions import (
    LLMGenerationError, InternalServerError, ServiceUnavailableException,
    BadRequestException
)
from shared.models import QCReport # Importe le modèle QCReport si nécessaire

logger = logging.getLogger(__name__)
settings = get_settings()

class RefinementEngine:
    """
    Moteur de Raffinement du Service Interaction et Raffinement.
    Prend le contenu original et le feedback (utilisateur ou QC) pour formuler
    des instructions précises pour le Service Génération afin d'améliorer le contenu.
    """
    def __init__(self, generation_service_url: str, kb_service_url: str):
        self.generation_service_url = generation_service_url
        self.kb_service_url = kb_service_url
        logger.info("RefinementEngine initialisé.")

    async def _get_kb_data_for_refinement(self, concept_id: Optional[UUID], level: str, style: str) -> Dict[str, Any]:
        """
        Récupère des données pertinentes de la KB pour aider au raffinement.
        (Ex: définitions alternatives, pièges, analogies pour un meilleur contexte).
        """
        kb_context = {}
        if concept_id:
            async with httpx.AsyncClient() as client:
                try:
                    # Exemple: obtenir des définitions intuitives ou formelles
                    resp_def = await client.get(f"{self.kb_service_url}/internal/concepts/{concept_id}/definitions", params={"type": "intuitive", "level": level})
                    resp_def.raise_for_status()
                    kb_context["intuitive_definitions"] = resp_def.json()

                    resp_pitfalls = await client.get(f"{self.kb_service_url}/internal/concepts/{concept_id}/pitfalls", params={"level": level})
                    resp_pitfalls.raise_for_status()
                    kb_context["pitfalls"] = resp_pitfalls.json()

                    # Ajouter d'autres données KB pertinentes
                except httpx.HTTPStatusError as e:
                    logger.warning(f"KB Service returned HTTP error during refinement context retrieval for concept {concept_id}: {e.response.text}")
                except httpx.RequestError as e:
                    logger.error(f"Network error calling KB Service during refinement context retrieval for concept {concept_id}: {e}")
                    # Ne pas lever d'exception ici, car le raffinement peut continuer sans KB complète
        return kb_context

    async def refine_content(self, 
                             content_latex: str, 
                             feedback: Dict[str, Any], 
                             block_type: str, 
                             level: str, 
                             style: str, 
                             context: Optional[Dict[str, Any]] = None) -> str:
        """
        Raffine un contenu existant basé sur un feedback (utilisateur ou QC).
        Args:
            content_latex (str): Le contenu original à raffiner en LaTeX.
            feedback (Dict[str, Any]): Dictionnaire du feedback analysé (type, details, location, confidence).
            block_type (str): Type du bloc de contenu.
            level (str): Niveau pédagogique cible.
            style (str): Style rédactionnel.
            context (Optional[Dict[str, Any]]): Contexte supplémentaire du projet/bloc.
        Returns:
            str: Le contenu raffiné en LaTeX.
        Raises:
            LLMGenerationError: Si le service de génération échoue.
            InternalServerError: Pour d'autres erreurs.
        """
        logger.info(f"Début du raffinement pour un bloc de type '{block_type}' avec feedback de type '{feedback.get('type')}'.")
        
        # Récupérer des informations supplémentaires de la KB si un concept_id est disponible dans le contexte
        concept_id = context.get('concept_id') if context else None
        kb_context = await self._get_kb_data_for_refinement(concept_id, level, style)

        # 1. Formuler les instructions de modification pour le LLM
        modification_instructions = self._formulate_llm_instructions(
            feedback, block_type, level, style, kb_context
        )
        logger.debug(f"Instructions de modification formulées: {modification_instructions[:200]}...")

        # 2. Construire le prompt ajusté pour le Service Génération
        # Le service de génération a une méthode spécifique pour le raffinement qui prend un prompt ajusté.
        adjusted_prompt_data = {
            "content_latex": content_latex,
            "feedback": feedback, # Passer le feedback complet pour que le service de génération puisse l'utiliser
            "block_type": block_type,
            "level": level,
            "style": style,
            "context": context # Passer le contexte original
        }
        
        # Le prompt final sera construit par le service de génération lui-même en utilisant son template 'refinement'.
        # Nous allons appeler l'endpoint de raffinement du service de génération.
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.generation_service_url}/internal/refine/content",
                    json=adjusted_prompt_data,
                    timeout=300.0 # Le raffinement peut prendre du temps
                )
                response.raise_for_status()
                refined_content = response.json().get("content_latex")
                logger.info(f"Contenu raffiné avec succès par le Generation Service.")
                return refined_content
            except httpx.HTTPStatusError as e:
                error_detail = e.response.text
                logger.error(f"Erreur HTTP lors de l'appel au Generation Service pour raffinement: {e.response.status_code} - {error_detail}")
                raise LLMGenerationError(detail=f"Échec du raffinement par le LLM: {error_detail}")
            except httpx.RequestError as e:
                logger.error(f"Erreur réseau lors de l'appel au Generation Service pour raffinement: {e}")
                raise ServiceUnavailableException(detail="Le Generation Service n'est pas disponible pour le raffinement.")
            except Exception as e:
                logger.critical(f"Erreur inattendue lors de l'appel au Generation Service pour raffinement: {e}", exc_info=True)
                raise InternalServerError(detail=f"Erreur interne lors du raffinement: {e}")

    def _formulate_llm_instructions(self, 
                                    feedback: Dict[str, Any], 
                                    block_type: str, 
                                    level: str, 
                                    style: str, 
                                    kb_context: Dict[str, Any]) -> str:
        """
        Formule des instructions textuelles détaillées pour le LLM basé sur le feedback.
        Ces instructions seront intégrées dans le prompt du service de génération.
        """
        feedback_type = feedback.get('type')
        feedback_details = feedback.get('details', 'Aucun détail fourni.')
        feedback_location = feedback.get('location')

        instructions = f"Le contenu doit être amélioré. Voici le feedback:\n\n"

        if feedback_type == 'math_error':
            instructions += f"**Correction mathématique requise:** Une erreur mathématique a été détectée. Détails: {feedback_details}. "
            if feedback_location:
                instructions += f"L'erreur est localisée à: {feedback_location}. "
            instructions += "Corrige précisément le raisonnement, la formule ou les calculs pour assurer l'exactitude mathématique. "
            # Ajouter des définitions formelles ou théorèmes de la KB si pertinents
            if kb_context.get("formal_definitions"):
                instructions += f"Référez-vous aux définitions formelles suivantes: {kb_context['formal_definitions']}. "

        elif feedback_type == 'clarity_issue':
            instructions += f"**Amélioration de la clarté requise:** L'explication n'est pas suffisamment claire ou intuitive. Détails: {feedback_details}. "
            if feedback_location:
                instructions += f"La partie concernée est: {feedback_location}. "
            instructions += f"Reformule cette partie pour qu'elle soit plus facile à comprendre pour un étudiant de niveau {level}, dans le style {style}. "
            if kb_context.get("analogies"):
                instructions += f"Considérez l'ajout d'une analogie pertinente comme: {kb_context['analogies'][0].get('description_latex') if kb_context['analogies'] else ''}. "
            if kb_context.get("pitfalls"):
                instructions += f"Abordez le piège courant suivant: {kb_context['pitfalls'][0].get('description_short') if kb_context['pitfalls'] else ''}. "

        elif feedback_type == 'style_mismatch':
            instructions += f"**Ajustement stylistique nécessaire:** Le ton ou la formulation ne correspondent pas au style '{style}'. Détails: {feedback_details}. "
            instructions += f"Réécrivez le contenu pour qu'il soit pleinement conforme au style {style} pour le niveau {level}."

        elif feedback_type == 'suggestion':
            instructions += f"**Suggestion d'amélioration:** L'utilisateur a suggéré: {feedback_details}. "
            instructions += "Incorporez cette suggestion de manière appropriée dans le contenu."
        
        elif feedback_type == 'qc_issue':
            # Pour les problèmes QC génériques non catégorisés plus précisément
            instructions += f"**Problème détecté par le Contrôle Qualité:** Le rapport QC a signalé un problème. Détails: {feedback_details}. "
            instructions += "Veuillez réévaluer et corriger le contenu pour améliorer sa qualité globale."

        else:
            instructions += f"**Demande de modification générale:** {feedback_details}. "
            instructions += "Veuillez réviser le contenu en fonction de ce feedback."
        
        instructions += "\n\nVotre réponse doit être uniquement le contenu LaTeX corrigé et amélioré."
        return instructions

