# Fichier placeholder pour run_benchmarks.py
# scripts/run_benchmarks.py

import asyncio
import httpx
import logging
import csv
import time
from typing import Dict, Any, List, Optional
import os

# Configure le logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URLs des services backend
GENERATION_SERVICE_URL = "http://localhost:8000/internal" # Remplacez par l'URL réelle si différente
QC_SERVICE_URL = "http://localhost:8000/internal"       # Remplacez par l'URL réelle si différente

# Chemin vers le fichier de résultats CSV
RESULTS_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../docs/benchmarks/results_table.csv")

# --- Configurations des Benchmarks ---
# Ces configurations devraient idéalement être chargées depuis un fichier YAML ou une DB.

# LLMs à tester (doivent correspondre à ceux configurés dans generation-service)
LLMS_TO_BENCHMARK = [
    {"name": "gpt-4-turbo", "provider": "openai", "cost_per_token_input": 0.00001, "cost_per_token_output": 0.00003},
    {"name": "gemini-pro", "provider": "google", "cost_per_token_input": 0.00000125, "cost_per_token_output": 0.00000375},
    {"name": "claude-3-opus-20240229", "provider": "anthropic", "cost_per_token_input": 0.000015, "cost_per_token_output": 0.000075},
]

# Tâches de benchmark (exemples simplifiés)
# En réalité, ces données proviendraient de jeux de données de benchmark plus complexes.
BENCHMARK_TASKS = [
    {
        "task_type": "definition",
        "content_subtype": "formelle",
        "level": "L2",
        "style": "Bourbaki",
        "prompt_template_name": "Définition Formelle", # Nom du template dans templates.yaml
        "context_data": {
            "concept_name": "Espace Vectoriel",
            "formal_definition_from_KB": "Soit $E$ un ensemble non vide, muni d'une loi de composition interne, notée $+$, et d'une loi de composition externe, notée $\\cdot$, à valeurs dans un corps $\\mathbb{K}$.",
            "prerequisite_concepts_names": "Corps (Mathématiques), Groupe (Mathématiques)"
        },
        "expected_response_length_tokens": 500, # Estimation
        "endpoint": "/generate/definition" # Endpoint du generation-service
    },
    {
        "task_type": "intuition",
        "content_subtype": "intuitive",
        "level": "L2",
        "style": "Feynman",
        "prompt_template_name": "Explication Intuitive et Analogie",
        "context_data": {
            "concept_name": "Dérivée",
            "formal_definition_from_KB": "$\\lim_{x \\to a} \\frac{f(x) - f(a)}{x - a}$",
            "pitfall_description_from_KB": "Confondre dérivée et primitive.",
            "verified_analogy_from_KB": "La pente d'une montagne."
        },
        "expected_response_length_tokens": 300,
        "endpoint": "/generate/intuition"
    },
    {
        "task_type": "proof_skeleton",
        "content_subtype": "default",
        "level": "M1",
        "style": "Hybride",
        "prompt_template_name": "Squelette de Preuve",
        "context_data": {
            "theorem_name": "Théorème de la Dérivée d'une Somme",
            "theorem_statement_from_KB": "Si $f$ et $g$ sont deux fonctions dérivables en $x$, alors $(f+g)'(x) = f'(x) + g'(x)$.",
            "proof_ideas_from_KB": "Définition de la dérivée, propriété de la limite d'une somme."
        },
        "expected_response_length_tokens": 800,
        "endpoint": "/generate/proof-skeleton"
    },
    # Ajoutez d'autres tâches de benchmark ici (exercices, raffinement, etc.)
]

async def call_generation_service(llm_name: str, task_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Appelle le service de génération pour obtenir du contenu d'un LLM.
    Retourne le contenu généré, la latence et le nombre de tokens.
    """
    endpoint = task_config["endpoint"]
    payload = {
        "llm_name": llm_name,
        "content_type": task_config["task_type"], # Le type de contenu pour le prompt builder
        "level": task_config["level"],
        "style": task_config["style"],
        "context_data": task_config["context_data"]
    }
    
    # Pour l'endpoint /generate/exercise, le payload est différent.
    # Il faudrait adapter le payload en fonction de l'endpoint/task_type.
    # Pour simplifier, nous allons juste envoyer le payload générique pour le moment.
    if endpoint == "/generate/exercise":
        payload["exercise_type"] = task_config.get("exercise_type", "calculation")
        payload["difficulty"] = task_config.get("difficulty", "medium")
        payload["num_exercises"] = task_config.get("num_exercises", 1)
        # Supprimer les champs non pertinents pour l'exercice
        del payload["content_type"]
        del payload["context_data"]
    elif endpoint == "/refine/content":
        payload["content_latex"] = task_config["content_latex_original"]
        payload["feedback"] = task_config["feedback_data"]
        # Supprimer les champs non pertinents
        del payload["prompt_template_name"]
        del payload["context_data"]


    start_time = time.time()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GENERATION_SERVICE_URL}{endpoint}",
                json=payload,
                timeout=300.0 # Long timeout pour les LLMs
            )
            response.raise_for_status()
            result = response.json()
            latency = time.time() - start_time
            
            # Estimer le nombre de tokens (très basique, un vrai tokenizer serait nécessaire)
            # Pour l'exemple, nous utilisons une estimation basée sur la longueur du texte.
            # Un token est environ 4 caractères pour l'anglais, peut varier pour LaTeX.
            # Le service de génération devrait idéalement retourner le nombre de tokens utilisés.
            generated_content = result.get("content_latex") or result.get("exercises", [{}])[0].get("prompt_latex")
            num_tokens = len(generated_content) / 4 if generated_content else 0

            return {"content": result, "latency": latency, "num_tokens": num_tokens}
    except httpx.HTTPStatusError as e:
        logger.error(f"Erreur HTTP lors de l'appel au Generation Service ({llm_name}, {endpoint}): {e.response.status_code} - {e.response.text}")
        return {"error": f"HTTP Error {e.response.status_code}: {e.response.text}"}
    except httpx.RequestError as e:
        logger.error(f"Erreur réseau lors de l'appel au Generation Service ({llm_name}, {endpoint}): {e}")
        return {"error": f"Network Error: {e}"}
    except Exception as e:
        logger.error(f"Erreur inattendue lors de l'appel au Generation Service ({llm_name}, {endpoint}): {e}", exc_info=True)
        return {"error": f"Unhandled Error: {e}"}

async def call_qc_service(content_to_qc: Dict[str, Any], task_type: str, level: str, style: str) -> Dict[str, Any]:
    """
    Appelle le service QC pour obtenir un rapport de qualité.
    """
    # L'endpoint de QC dépend du type de contenu
    endpoint = "/analyze/content-block"
    payload = {
        "block_id": "benchmark_block_id", # Placeholder ID
        "content_latex": content_to_qc.get("content_latex"),
        "block_type": task_type,
        "level": level,
        "style": style,
        "context": {}
    }
    
    if task_type == "exercise":
        endpoint = "/analyze/exercise"
        payload = {
            "exercise_id": "benchmark_exercise_id",
            "prompt_latex": content_to_qc.get("exercises", [{}])[0].get("prompt_latex"),
            "solution_latex": content_to_qc.get("exercises", [{}])[0].get("solution_latex"),
            "level": level,
            "exercise_type": task_type, # Ou un type d'exercice plus spécifique
            "context": {}
        }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{QC_SERVICE_URL}{endpoint}",
                json=payload,
                timeout=180.0 # Long timeout pour le QC
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Erreur HTTP lors de l'appel au QC Service ({endpoint}): {e.response.status_code} - {e.response.text}")
        return {"error": f"HTTP Error {e.response.status_code}: {e.response.text}"}
    except httpx.RequestError as e:
        logger.error(f"Erreur réseau lors de l'appel au QC Service ({endpoint}): {e}")
        return {"error": f"Network Error: {e}"}
    except Exception as e:
        logger.error(f"Erreur inattendue lors de l'appel au QC Service ({endpoint}): {e}", exc_info=True)
        return {"error": f"Unhandled Error: {e}"}


async def run_benchmark_task(llm_config: Dict[str, Any], task_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Exécute un benchmark pour un LLM et une tâche spécifique.
    """
    llm_name = llm_config["name"]
    logger.info(f"Exécution du benchmark pour LLM: {llm_name}, Tâche: {task_config['task_type']} ({task_config['level']}, {task_config['style']})")

    # 1. Appel au service de génération
    gen_result = await call_generation_service(llm_name, task_config)

    if "error" in gen_result:
        return {
            "task_type": task_config["task_type"],
            "content_subtype": task_config["content_subtype"],
            "level": task_config["level"],
            "style": task_config["style"],
            "llm_name": llm_name,
            "qc_score_avg": 0.0,
            "qc_failure_rate": 1.0, # Échec si la génération échoue
            "latency_avg_s": gen_result.get("latency", 0.0),
            "throughput_tokens_per_s": 0.0,
            "cost_per_task_usd": 0.0,
            "api_failure_rate": 1.0,
            "notes": f"Génération échouée: {gen_result['error']}"
        }

    generated_content = gen_result["content"]
    latency = gen_result["latency"]
    num_tokens = gen_result["num_tokens"]

    # 2. Appel au service QC
    qc_report = await call_qc_service(generated_content, task_config["task_type"], task_config["level"], task_config["style"])

    qc_score_avg = 0.0
    qc_failure_rate = 1.0 # Par défaut, échec du QC
    if qc_report and "overall_score" in qc_report:
        qc_score_avg = qc_report["overall_score"]
        qc_failure_rate = 0.0 if qc_report["status"] == "passed" else 1.0 # Simplifié
        if qc_report["status"] == "partial_success": qc_failure_rate = 0.5 # Ajustement

    # Calcul du coût
    cost_per_task_usd = (llm_config["cost_per_token_input"] * (task_config.get("prompt_length_estimate", 0) or num_tokens)) + \
                        (llm_config["cost_per_token_output"] * num_tokens)

    throughput_tokens_per_s = num_tokens / latency if latency > 0 else 0

    return {
        "task_type": task_config["task_type"],
        "content_subtype": task_config["content_subtype"],
        "level": task_config["level"],
        "style": task_config["style"],
        "llm_name": llm_name,
        "qc_score_avg": qc_score_avg,
        "qc_failure_rate": qc_failure_rate,
        "latency_avg_s": latency,
        "throughput_tokens_per_s": throughput_tokens_per_s,
        "cost_per_task_usd": cost_per_task_usd,
        "api_failure_rate": 0.0, # Supposons que l'API de génération a réussi ici
        "notes": qc_report.get("error") if "error" in qc_report else ""
    }

async def main():
    logger.info("Démarrage de l'exécution des benchmarks LLM...")

    # Assurez-vous que le fichier de résultats CSV existe avec les en-têtes
    headers = [
        "task_type", "content_subtype", "level", "style", "llm_name",
        "qc_score_avg", "qc_failure_rate", "latency_avg_s",
        "throughput_tokens_per_s", "cost_per_task_usd", "api_failure_rate", "notes"
    ]
    if not os.path.exists(RESULTS_FILE_PATH):
        with open(RESULTS_FILE_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
        logger.info(f"Fichier de résultats CSV créé à: {RESULTS_FILE_PATH}")
    else:
        logger.info(f"Fichier de résultats CSV existant: {RESULTS_FILE_PATH}. Les nouveaux résultats seront ajoutés.")

    all_results = []
    for llm in LLMS_TO_BENCHMARK:
        for task in BENCHMARK_TASKS:
            result = await run_benchmark_task(llm, task)
            all_results.append(result)
            # Écrire le résultat immédiatement pour ne pas perdre de données en cas d'interruption
            with open(RESULTS_FILE_PATH, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writerow(result)
            logger.info(f"Résultat écrit pour {llm['name']} / {task['task_type']}")

    logger.info("Exécution des benchmarks terminée. Résultats dans results_table.csv")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except httpx.RequestError as e:
        logger.error(f"Impossible de se connecter à un service backend. Assurez-vous que les services de génération et QC sont en cours d'exécution. Erreur: {e}")
    except Exception as e:
        logger.critical(f"Une erreur inattendue est survenue lors de l'exécution des benchmarks: {e}", exc_info=True)
