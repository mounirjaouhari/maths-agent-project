# Fichier placeholder pour llm_selector.py
# backend/generation-service/generation/llm_selector.py

import logging
import httpx
from typing import Dict, Any, List, Optional
from uuid import UUID

from shared.config import get_settings
from shared.exceptions import InternalServerError, ServiceUnavailableException, BadRequestException

logger = logging.getLogger(__name__)
settings = get_settings()

class LLMSelector:
    """
    Implémente la logique de sélection dynamique du LLM le plus approprié
    pour chaque requête de génération, en utilisant les benchmarks et les critères définis.
    """
    def __init__(self, kb_service_url: str):
        self.kb_service_url = kb_service_url
        # Dans un système réel, les configurations LLM et les benchmarks seraient chargés
        # depuis une base de données ou un service de configuration.
        # Pour l'exemple, nous allons les définir en dur ou les charger depuis un fichier.
        self.llm_configs = self._load_llm_configurations()
        self.llm_benchmarks = self._load_llm_benchmarks() # Simule le chargement des résultats de benchmark
        logger.info("LLMSelector initialisé et configurations/benchmarks chargés.")

    def _load_llm_configurations(self) -> Dict[str, Dict[str, Any]]:
        """
        Charge les configurations des LLMs disponibles.
        En production, cela viendrait d'un service de configuration ou d'une DB.
        """
        # Exemple de configuration de LLMs. Les clés API sont chargées via settings.
        return {
            "gpt-4-turbo": {
                "name": "gpt-4-turbo",
                "provider": "openai",
                "cost_per_token_input": 0.00001, # Exemple de coût
                "cost_per_token_output": 0.00003,
                "max_tokens": 4096,
                "capabilities": ["complex_reasoning", "code_generation", "high_accuracy"],
                "default_params": {"temperature": 0.7, "top_p": 1.0}
            },
            "gemini-pro": {
                "name": "gemini-pro",
                "provider": "google",
                "cost_per_token_input": 0.00000125,
                "cost_per_token_output": 0.00000375,
                "max_tokens": 8192,
                "capabilities": ["creative_text", "multimodal"],
                "default_params": {"temperature": 0.9, "top_p": 0.95, "top_k": 40}
            },
            "claude-3-opus-20240229": {
                "name": "claude-3-opus-20240229",
                "provider": "anthropic",
                "cost_per_token_input": 0.000015,
                "cost_per_token_output": 0.000075,
                "max_tokens": 4096,
                "capabilities": ["long_context", "nuance", "safety"],
                "default_params": {"temperature": 0.7, "top_p": 0.99, "top_k": 0}
            },
            # Ajoutez d'autres modèles si nécessaire
        }

    def _load_llm_benchmarks(self) -> Dict[str, Dict[str, Any]]:
        """
        Charge les résultats des benchmarks internes.
        En production, cela viendrait d'une DB ou d'un service de données.
        Pour l'exemple, nous simulerons des données.
        La clé est une combinaison de (task_type, level, style, llm_name).
        """
        # Exemple de données de benchmark simulées
        return {
            ("definition", "L2", "Bourbaki", "gpt-4-turbo"): {"qc_score_avg": 92.5, "latency_avg_s": 3.2, "cost_per_task_usd": 0.015},
            ("definition", "L2", "Bourbaki", "gemini-pro"): {"qc_score_avg": 88.1, "latency_avg_s": 2.8, "cost_per_task_usd": 0.012},
            ("definition", "L2", "Bourbaki", "claude-3-opus-20240229"): {"qc_score_avg": 89.0, "latency_avg_s": 3.5, "cost_per_task_usd": 0.02},

            ("intuition", "L2", "Feynman", "gpt-4-turbo"): {"qc_score_avg": 78.9, "latency_avg_s": 2.5, "cost_per_task_usd": 0.01},
            ("intuition", "L2", "Feynman", "gemini-pro"): {"qc_score_avg": 85.0, "latency_avg_s": 2.0, "cost_per_task_usd": 0.008},
            ("intuition", "L2", "Feynman", "claude-3-opus-20240229"): {"qc_score_avg": 91.0, "latency_avg_s": 4.0, "cost_per_task_usd": 0.03},

            ("proof_skeleton", "M1", "Hybride", "gpt-4-turbo"): {"qc_score_avg": 88.0, "latency_avg_s": 5.5, "cost_per_task_usd": 0.03},
            ("proof_skeleton", "M1", "Hybride", "gemini-pro"): {"qc_score_avg": 80.0, "latency_avg_s": 4.5, "cost_per_task_usd": 0.025},

            # Ajoutez d'autres benchmarks pour d'autres tâches, niveaux, styles
        }

    async def select_best_llm(self, 
                              task_type: str, 
                              level: str, 
                              style: str, 
                              prompt_length_estimate: int = 500, # Estimation de la longueur du prompt pour le coût
                              response_length_estimate: int = 1000) -> Dict[str, Any]:
        """
        Sélectionne le LLM le plus approprié pour une tâche de génération donnée.
        Args:
            task_type (str): Type de contenu à générer (ex: 'definition', 'intuition').
            level (str): Niveau pédagogique cible.
            style (str): Style rédactionnel.
            prompt_length_estimate (int): Estimation de la longueur du prompt en tokens.
            response_length_estimate (int): Estimation de la longueur de la réponse en tokens.
        Returns:
            Dict[str, Any]: La configuration du LLM sélectionné (nom, provider, default_params, etc.).
        Raises:
            InternalServerError: Si aucun LLM approprié n'est trouvé.
        """
        best_llm_config = None
        best_composite_score = -1.0

        available_llms = self.llm_configs.values() # Tous les LLMs configurés

        for llm_config in available_llms:
            llm_name = llm_config["name"]
            
            # Critère 1: Disponibilité (simplifié, en production, on vérifierait l'état réel)
            # Pour l'exemple, on suppose que tous les LLMs configurés sont "disponibles"
            # if not await self._check_llm_availability(llm_config["provider"]):
            #     continue

            # Critère 2: Performance mesurée (via benchmarks)
            benchmark_key = (task_type, level, style, llm_name)
            benchmarks = self.llm_benchmarks.get(benchmark_key)
            
            if not benchmarks:
                # Si pas de benchmark spécifique, utiliser un benchmark par défaut ou pénaliser
                logger.warning(f"Pas de benchmark trouvé pour {benchmark_key}. Utilisation de valeurs par défaut/pénalisées.")
                qc_score = 50.0 # Pénalité si pas de données
                latency = 10.0
                cost = 0.05
            else:
                qc_score = benchmarks["qc_score_avg"]
                latency = benchmarks["latency_avg_s"]
                cost = benchmarks["cost_per_task_usd"]
            
            # Critère 3: Coût estimé (calculé à la volée si non dans benchmark)
            if "cost_per_token_input" in llm_config:
                estimated_cost = (llm_config["cost_per_token_input"] * prompt_length_estimate) + \
                                 (llm_config["cost_per_token_output"] * response_length_estimate)
                if cost == 0.0: # Si pas de coût dans benchmark, utiliser l'estimation
                    cost = estimated_cost
            
            # Critère 4: Capacités spécifiques du LLM (non implémenté ici, mais pourrait filtrer/booster)
            # if "complex_reasoning" in llm_config["capabilities"] and task_type == "proof_skeleton":
            #     qc_score *= 1.1 # Booster le score pour les capacités pertinentes

            # Calcul du score composite (pondération des critères)
            # Plus le score QC est élevé, mieux c'est. Plus la latence/coût sont bas, mieux c'est.
            # Normaliser les valeurs pour qu'elles soient comparables.
            # Ceci est une heuristique simple, à affiner avec des données réelles.
            
            # Éviter la division par zéro ou par des valeurs très faibles
            normalized_latency = 1.0 / (latency + 0.1) 
            normalized_cost = 1.0 / (cost + 0.001) 
            
            # Pondération: la qualité est la plus importante, puis la latence, puis le coût
            composite_score = (qc_score * 0.5) + (normalized_latency * 0.3) + (normalized_cost * 0.2)
            
            if composite_score > best_composite_score:
                best_composite_score = composite_score
                best_llm_config = llm_config
        
        if best_llm_config is None:
            # Fallback si aucun LLM n'a été sélectionné (très improbable si llm_configs n'est pas vide)
            # Retourner un LLM par défaut fiable
            logger.warning("Aucun LLM optimal trouvé, retour au LLM par défaut (gpt-4-turbo).")
            return self.llm_configs.get("gpt-4-turbo") # Fallback à un LLM connu pour être fiable

        logger.info(f"LLM sélectionné pour la tâche ({task_type}, {level}, {style}): {best_llm_config['name']} (Score composite: {best_composite_score:.2f})")
        return best_llm_config

    # async def _check_llm_availability(self, provider: str) -> bool:
    #     """
    #     Vérifie la disponibilité réelle de l'API d'un fournisseur LLM.
    #     Ceci nécessiterait des endpoints de santé ou des pings réels aux APIs LLM.
    #     """
    #     # Placeholder: en production, cela interrogerait un service de monitoring ou tenterait un ping.
    #     return True 
