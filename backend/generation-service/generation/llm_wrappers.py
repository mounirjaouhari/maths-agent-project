# Fichier placeholder pour llm_wrappers.py
# backend/generation-service/generation/llm_wrappers.py

import openai
import google.generativeai as genai
import anthropic
import logging
from typing import Dict, Any, Optional

from shared.exceptions import LLMAPIError, InternalServerError

logger = logging.getLogger(__name__)

class LLMWrapper:
    """
    Fournit une interface standardisée pour interagir avec différents SDKs/APIs de fournisseurs de LLM (OpenAI, Gemini, Claude).
    Gère les spécificités de chaque API et les erreurs de base.
    """
    def __init__(self, openai_api_key: Optional[str] = None, 
                 google_ai_api_key: Optional[str] = None, 
                 anthropic_api_key: Optional[str] = None):
        
        # Initialisation des clients LLM avec leurs clés API
        if openai_api_key:
            openai.api_key = openai_api_key
            logger.info("OpenAI API key loaded.")
        else:
            logger.warning("OpenAI API key not provided.")

        if google_ai_api_key:
            genai.configure(api_key=google_ai_api_key)
            logger.info("Google AI API key loaded.")
        else:
            logger.warning("Google AI API key not provided.")
        
        self.anthropic_client = None
        if anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
            logger.info("Anthropic API key loaded.")
        else:
            logger.warning("Anthropic API key not provided.")

    async def call_llm(self, model_name: str, prompt: str, params: Dict[str, Any]) -> str:
        """
        Appelle le LLM spécifié avec le prompt et les paramètres donnés.
        Args:
            model_name (str): Le nom du modèle LLM à utiliser (ex: "gpt-4", "gemini-pro", "claude-3-opus").
            prompt (str): Le prompt textuel à envoyer au LLM.
            params (Dict[str, Any]): Paramètres de génération (ex: temperature, max_tokens).
        Returns:
            str: Le texte généré par le LLM.
        Raises:
            LLMAPIError: Si une erreur spécifique à l'API LLM survient.
            InternalServerError: Pour d'autres erreurs inattendues.
        """
        try:
            if model_name.startswith('gpt'):
                return await self._call_openai(model_name, prompt, params)
            elif model_name.startswith('gemini'):
                return await self._call_gemini(model_name, prompt, params)
            elif model_name.startswith('claude'):
                return await self._call_anthropic(model_name, prompt, params)
            else:
                raise BadRequestException(detail=f"Modèle LLM non supporté: {model_name}")
        except LLMAPIError:
            raise # Re-lève l'exception spécifique LLMAPIError
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'appel LLM pour le modèle {model_name}: {e}", exc_info=True)
            raise InternalServerError(detail=f"Erreur interne lors de l'appel au LLM {model_name}.")

    async def _call_openai(self, model_name: str, prompt: str, params: Dict[str, Any]) -> str:
        """Appelle l'API OpenAI."""
        if not openai.api_key:
            raise LLMAPIError(llm_name="OpenAI", original_detail="Clé API OpenAI non configurée.")

        try:
            # Adapter les paramètres génériques aux paramètres spécifiques de l'API OpenAI
            openai_params = {
                "model": model_name,
                "prompt": prompt,
                "max_tokens": params.get("max_tokens", 1024), # Valeur par défaut raisonnable
                "temperature": params.get("temperature", 0.7),
                "top_p": params.get("top_p", 1.0),
                "frequency_penalty": params.get("frequency_penalty", 0.0),
                "presence_penalty": params.get("presence_penalty", 0.0),
                **params.get("openai_specific_params", {}) # Permettre des paramètres spécifiques
            }
            
            # Utilisation de openai.Completion.create pour les modèles de complétion (legacy)
            # Pour les modèles de chat (gpt-3.5-turbo, gpt-4), il faudrait utiliser openai.ChatCompletion.create
            # et formater le prompt en messages.
            # Pour simplifier, nous utilisons ici un appel générique de complétion.
            # Dans un système réel, il faudrait distinguer les appels chat/completion.
            
            if "gpt-3.5-turbo" in model_name or "gpt-4" in model_name:
                # Exemple pour les modèles de chat
                response = await openai.ChatCompletion.acreate( # Utilisation de acreate pour asynchrone
                    model=model_name,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    **{k: v for k, v in openai_params.items() if k not in ["model", "prompt"]} # Exclure model/prompt
                )
                return response.choices[0].message.content.strip()
            else:
                # Pour les anciens modèles de complétion
                response = await openai.Completion.acreate(**openai_params)
                return response.choices[0].text.strip()

        except openai.error.AuthenticationError as e:
            raise LLMAPIError(llm_name="OpenAI", original_detail=f"Erreur d'authentification: {e.user_message}")
        except openai.error.RateLimitError as e:
            raise LLMAPIError(llm_name="OpenAI", original_detail=f"Limite de taux atteinte: {e.user_message}")
        except openai.error.APIError as e:
            raise LLMAPIError(llm_name="OpenAI", original_detail=f"Erreur API OpenAI: {e.user_message}")
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'appel OpenAI {model_name}: {e}", exc_info=True)
            raise LLMAPIError(llm_name="OpenAI", original_detail=f"Erreur inconnue: {e}")

    async def _call_gemini(self, model_name: str, prompt: str, params: Dict[str, Any]) -> str:
        """Appelle l'API Google AI (Gemini)."""
        # genai.configure() doit avoir été appelé avec la clé API au démarrage de l'app
        try:
            # Adapter les paramètres génériques aux paramètres spécifiques de l'API Gemini
            gemini_params = {
                "temperature": params.get("temperature", 0.7),
                "candidate_count": 1,
                "max_output_tokens": params.get("max_tokens", 1024),
                "top_p": params.get("top_p", 1.0),
                "top_k": params.get("top_k", 40),
                **params.get("gemini_specific_params", {})
            }
            
            # Utiliser le modèle spécifique
            model = genai.GenerativeModel(model_name)
            
            # L'appel générera du contenu de manière asynchrone
            response = await model.generate_content_async(prompt, generation_config=gemini_params)
            
            # Vérifier si la réponse contient du texte
            if response.candidates and response.candidates[0].content.parts:
                return response.candidates[0].content.parts[0].text.strip()
            else:
                # Gérer les cas où le modèle ne génère pas de contenu (ex: bloqué par les filtres de sécurité)
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    block_reason = response.prompt_feedback.block_reason.name
                    raise LLMAPIError(llm_name="Gemini", original_detail=f"Contenu bloqué par le filtre de sécurité: {block_reason}")
                raise LLMAPIError(llm_name="Gemini", original_detail="Aucun contenu généré par le modèle.")

        except Exception as e:
            logger.error(f"Erreur lors de l'appel Gemini {model_name}: {e}", exc_info=True)
            raise LLMAPIError(llm_name="Gemini", original_detail=f"Erreur inconnue: {e}")

    async def _call_anthropic(self, model_name: str, prompt: str, params: Dict[str, Any]) -> str:
        """Appelle l'API Anthropic (Claude)."""
        if not self.anthropic_client:
            raise LLMAPIError(llm_name="Anthropic", original_detail="Client Anthropic non initialisé (clé API manquante).")

        try:
            # Adapter les paramètres génériques aux paramètres spécifiques de l'API Anthropic
            anthropic_params = {
                "model": model_name,
                "prompt": f"{anthropic.HUMAN_PROMPT} {prompt}{anthropic.AI_PROMPT}", # Format spécifique Anthropic
                "max_tokens_to_sample": params.get("max_tokens", 1024),
                "temperature": params.get("temperature", 0.7),
                "top_p": params.get("top_p", 1.0),
                "top_k": params.get("top_k", 0), # 0 signifie désactivé pour top_k
                **params.get("anthropic_specific_params", {})
            }
            
            response = await self.anthropic_client.completions.create(**anthropic_params)
            return response.completion.strip()
        except anthropic.APIError as e:
            raise LLMAPIError(llm_name="Anthropic", original_detail=f"Erreur API Anthropic: {e.response.text}")
        except Exception as e:
            logger.error(f"Erreur lors de l'appel Anthropic {model_name}: {e}", exc_info=True)
            raise LLMAPIError(llm_name="Anthropic", original_detail=f"Erreur inconnue: {e}")

