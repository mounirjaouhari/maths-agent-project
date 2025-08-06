# Fichier placeholder pour populate_kb.py
# scripts/populate_kb.py

import asyncio
import httpx
import logging
from uuid import UUID
from datetime import datetime, timezone

# Configure le logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URL du service de persistance (où la KB est stockée)
# En production, cette URL serait configurée via des variables d'environnement.
# Pour le développement local, assurez-vous que le persistence-service est en cours d'exécution.
PERSISTENCE_SERVICE_URL = "http://localhost:8000/internal" # Remplacez par l'URL réelle si différente

# --- Données de la Base de Connaissances à peupler ---
# Ces données sont des exemples simplifiés. En réalité, elles seraient beaucoup plus riches.

CONCEPTS_DATA = [
    {
        "name": "Espace Vectoriel",
        "slug": "espace_vectoriel",
        "domain": "Algèbre Linéaire",
        "level_min": "L1",
        "level_max": "M2",
        "description_short": "Ensemble muni d'une addition et d'une multiplication par un scalaire.",
    },
    {
        "name": "Dérivée",
        "slug": "derivee",
        "domain": "Analyse",
        "level_min": "L1",
        "level_max": "M2",
        "description_short": "Mesure la vitesse de variation d'une fonction.",
    },
    {
        "name": "Limite de Fonction",
        "slug": "limite_fonction",
        "domain": "Analyse",
        "level_min": "L1",
        "level_max": "L2",
        "description_short": "Valeur vers laquelle une fonction tend lorsque la variable s'approche d'un point.",
    },
    {
        "name": "Intégrale",
        "slug": "integrale",
        "domain": "Analyse",
        "level_min": "L1",
        "level_max": "M2",
        "description_short": "Généralisation de la somme, utilisée pour calculer aires et volumes.",
    },
    {
        "name": "Corps (Mathématiques)",
        "slug": "corps_mathematiques",
        "domain": "Algèbre",
        "level_min": "L1",
        "level_max": "M2",
        "description_short": "Structure algébrique avec addition, soustraction, multiplication et division.",
    },
]

DEFINITIONS_DATA = [
    {
        "concept_slug": "espace_vectoriel",
        "type": "formelle",
        "level": "L1",
        "content_latex": "\\textbf{Définition (Espace Vectoriel).} Soit $E$ un ensemble non vide, muni d'une loi de composition interne, notée $+$, et d'une loi de composition externe, notée $\\cdot$, à valeurs dans un corps $\\mathbb{K}$. On dit que $(E, +, \\cdot)$ est un $\\mathbb{K}$-espace vectoriel si...",
        "source": "Bourbaki",
        "is_verified": True,
    },
    {
        "concept_slug": "derivee",
        "type": "formelle",
        "level": "L1",
        "content_latex": "\\textbf{Définition (Dérivée).} Soit $f: I \\to \\mathbb{R}$ une fonction définie sur un intervalle $I \\subset \\mathbb{R}$. La dérivée de $f$ en un point $a \\in I$ est la limite, si elle existe, du taux d'accroissement $\\lim_{x \\to a} \\frac{f(x) - f(a)}{x - a}$.",
        "source": "Standard",
        "is_verified": True,
    },
    {
        "concept_slug": "derivee",
        "type": "intuitive",
        "level": "L1",
        "content_latex": "La dérivée d'une fonction en un point, c'est comme la pente de la tangente à la courbe de la fonction à ce point. Elle nous dit à quelle vitesse la fonction change.",
        "source": "Feynman-like",
        "is_verified": True,
    },
    {
        "concept_slug": "limite_fonction",
        "type": "formelle",
        "level": "L1",
        "content_latex": "\\textbf{Définition (Limite de Fonction).} Soit $f: I \\to \\mathbb{R}$ et $a \\in \\mathbb{R}$. On dit que $f(x)$ tend vers $L$ lorsque $x$ tend vers $a$ si pour tout $\\epsilon > 0$, il existe $\\delta > 0$ tel que si $0 < |x-a| < \\delta$, alors $|f(x)-L| < \\epsilon$.",
        "source": "Standard",
        "is_verified": True,
    },
]

THEOREMS_DATA = [
    {
        "name": "Théorème de la Dérivée d'une Somme",
        "statement_latex": "Si $f$ et $g$ sont deux fonctions dérivables en $x$, alors $(f+g)'(x) = f'(x) + g'(x)$.",
        "proof_sketch_latex": "Utiliser la définition de la dérivée et la propriété de la limite d'une somme.",
        "is_verified": True,
    },
    {
        "name": "Théorème Fondamental de l'Analyse",
        "statement_latex": "Si $f$ est continue sur $[a,b]$ et $F$ est une primitive de $f$, alors $\\int_a^b f(x) dx = F(b) - F(a)$.",
        "proof_sketch_latex": "Lier l'intégrale à la dérivée.",
        "is_verified": True,
    },
]

PITFALLS_DATA = [
    {
        "concept_slug": "derivee",
        "description_short": "Confondre dérivée et primitive.",
        "explanation_latex": "La dérivée donne la pente, la primitive l'aire. Ce sont des opérations inverses.",
        "level": "L1",
        "is_verified": True,
    },
    {
        "concept_slug": "limite_fonction",
        "description_short": "Confondre limite et valeur de la fonction au point.",
        "explanation_latex": "La limite décrit le comportement *autour* du point, pas nécessairement *au* point.",
        "level": "L1",
        "is_verified": True,
    },
]

ANALOGIES_DATA = [
    {
        "concept_slug": "integrale",
        "title": "L'intégrale comme accumulation",
        "description_latex": "Pensez à l'intégrale comme à l'accumulation d'eau dans une baignoire. Si la fonction $f(x)$ représente le débit d'eau à chaque instant $x$, alors l'intégrale de $f(x)$ sur un intervalle représente la quantité totale d'eau accumulée pendant cet intervalle.",
        "domain": "Physique",
        "level": "L1",
        "is_verified": True,
    },
]

# Données pour les relations (prérequis, concept-théorème)
RELATIONS_DATA = {
    "prerequisites": [
        {"concept_slug": "derivee", "prerequisite_slug": "limite_fonction", "type": "required"},
        {"concept_slug": "espace_vectoriel", "prerequisite_slug": "corps_mathematiques", "type": "required"},
    ],
    "concept_theorem_relations": [
        {"concept_slug": "derivee", "theorem_name": "Théorème de la Dérivée d'une Somme", "relation_type": "uses"},
        {"concept_slug": "integrale", "theorem_name": "Théorème Fondamental de l'Analyse", "relation_type": "defines"},
    ]
}


async def get_entity_by_slug(entity_type: str, slug: str, client: httpx.AsyncClient) -> Optional[Dict]:
    """Récupère une entité par son slug depuis le Persistence Service (KB part)."""
    try:
        response = await client.get(f"{PERSISTENCE_SERVICE_URL}/mathematical_concepts/slug/{slug}")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        raise
    except httpx.RequestError as e:
        logger.error(f"Erreur réseau lors de la récupération de {entity_type} par slug {slug}: {e}")
        raise

async def get_theorem_by_name(theorem_name: str, client: httpx.AsyncClient) -> Optional[Dict]:
    """Récupère un théorème par son nom (nécessite un endpoint spécifique ou une liste)."""
    # Pour l'instant, le Persistence Service n'a pas d'endpoint get_by_name pour les théorèmes.
    # Nous allons simuler une recherche par liste ou ajouter un endpoint si nécessaire.
    # Alternativement, on pourrait lister tous les théorèmes et filtrer.
    try:
        response = await client.get(f"{PERSISTENCE_SERVICE_URL}/theorems")
        response.raise_for_status()
        theorems = response.json()
        return next((t for t in theorems if t.get("name") == theorem_name), None)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        raise
    except httpx.RequestError as e:
        logger.error(f"Erreur réseau lors de la récupération du théorème par nom {theorem_name}: {e}")
        raise


async def create_entity(entity_type: str, data: Dict, client: httpx.AsyncClient) -> Dict:
    """Crée une entité via le Persistence Service."""
    try:
        response = await client.post(f"{PERSISTENCE_SERVICE_URL}/{entity_type}", json=data)
        response.raise_for_status()
        logger.info(f"Créé: {entity_type} - {data.get('name') or data.get('description_short') or data.get('statement_latex')}")
        return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 409: # Conflit (déjà existant)
            logger.warning(f"{entity_type} déjà existant: {data.get('name') or data.get('description_short')}. Ignoré.")
            return {} # Retourne un dictionnaire vide si déjà existant
        logger.error(f"Erreur HTTP lors de la création de {entity_type}: {e.response.text}")
        raise
    except httpx.RequestError as e:
        logger.error(f"Erreur réseau lors de la création de {entity_type}: {e}")
        raise

async def populate_kb():
    """
    Peuple la Base de Connaissances avec des données initiales.
    """
    logger.info("Début du peuplement de la Base de Connaissances...")

    async with httpx.AsyncClient() as client:
        # 1. Peupler les concepts
        concept_map = {} # Pour stocker les IDs des concepts créés
        for concept_data in CONCEPTS_DATA:
            existing_concept = await get_entity_by_slug("mathematical_concepts", concept_data["slug"], client)
            if not existing_concept:
                created_concept = await create_entity("mathematical_concepts", concept_data, client)
                concept_map[concept_data["slug"]] = created_concept.get("concept_id")
            else:
                concept_map[concept_data["slug"]] = existing_concept.get("concept_id")
                logger.info(f"Concept '{concept_data['name']}' existe déjà.")

        # 2. Peupler les définitions
        for definition_data in DEFINITIONS_DATA:
            concept_id = concept_map.get(definition_data["concept_slug"])
            if concept_id:
                data_to_create = {**definition_data, "concept_id": concept_id}
                del data_to_create["concept_slug"] # Supprimer le slug qui n'est pas dans le modèle
                await create_entity("concept_definitions", data_to_create, client)
            else:
                logger.warning(f"Concept '{definition_data['concept_slug']}' non trouvé pour la définition. Ignoré.")

        # 3. Peupler les théorèmes
        theorem_map = {} # Pour stocker les IDs des théorèmes créés
        for theorem_data in THEOREMS_DATA:
            existing_theorem = await get_theorem_by_name(theorem_data["name"], client)
            if not existing_theorem:
                created_theorem = await create_entity("theorems", theorem_data, client)
                theorem_map[theorem_data["name"]] = created_theorem.get("theorem_id")
            else:
                theorem_map[theorem_data["name"]] = existing_theorem.get("theorem_id")
                logger.info(f"Théorème '{theorem_data['name']}' existe déjà.")

        # 4. Peupler les pièges pédagogiques
        for pitfall_data in PITFALLS_DATA:
            concept_id = concept_map.get(pitfall_data["concept_slug"])
            if concept_id:
                data_to_create = {**pitfall_data, "concept_id": concept_id}
                del data_to_create["concept_slug"]
                await create_entity("pedagogical_pitfalls", data_to_create, client)
            else:
                logger.warning(f"Concept '{pitfall_data['concept_slug']}' non trouvé pour le piège. Ignoré.")

        # 5. Peupler les analogies
        for analogy_data in ANALOGIES_DATA:
            concept_id = concept_map.get(analogy_data["concept_slug"])
            if concept_id:
                data_to_create = {**analogy_data, "concept_id": concept_id}
                del data_to_create["concept_slug"]
                await create_entity("pedagogical_analogies", data_to_create, client)
            else:
                logger.warning(f"Concept '{analogy_data['concept_slug']}' non trouvé pour l'analogie. Ignoré.")

        # 6. Peupler les relations (prérequis, concept-théorème)
        logger.info("Peuplement des relations...")
        for prereq_data in RELATIONS_DATA["prerequisites"]:
            concept_id = concept_map.get(prereq_data["concept_slug"])
            prerequisite_concept_id = concept_map.get(prereq_data["prerequisite_slug"])
            if concept_id and prerequisite_concept_id:
                data_to_create = {
                    "concept_id": concept_id,
                    "prerequisite_concept_id": prerequisite_concept_id,
                    "type": prereq_data["type"]
                }
                # Il faudrait un endpoint spécifique pour les tables de jointure
                # ou les gérer via les dépôts principaux (ex: add_prerequisite_to_concept)
                # Pour l'exemple, nous allons simuler la création si l'endpoint existait.
                try:
                    await client.post(f"{PERSISTENCE_SERVICE_URL}/concept_prerequisites", json=data_to_create)
                    logger.info(f"Relation prérequis créée: {prereq_data['concept_slug']} REQUIERT {prereq_data['prerequisite_slug']}")
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 409:
                        logger.warning(f"Relation prérequis déjà existante: {prereq_data}. Ignoré.")
                    else:
                        logger.error(f"Erreur lors de la création de la relation prérequis {prereq_data}: {e.response.text}")
                except httpx.RequestError as e:
                    logger.error(f"Erreur réseau lors de la création de la relation prérequis {prereq_data}: {e}")
            else:
                logger.warning(f"Concepts non trouvés pour la relation prérequis: {prereq_data}. Ignoré.")

        for rel_data in RELATIONS_DATA["concept_theorem_relations"]:
            concept_id = concept_map.get(rel_data["concept_slug"])
            theorem_id = theorem_map.get(rel_data["theorem_name"])
            if concept_id and theorem_id:
                data_to_create = {
                    "concept_id": concept_id,
                    "theorem_id": theorem_id,
                    "relation_type": rel_data["relation_type"]
                }
                try:
                    await client.post(f"{PERSISTENCE_SERVICE_URL}/concept_theorem_relations", json=data_to_create)
                    logger.info(f"Relation concept-théorème créée: {rel_data['concept_slug']} {rel_data['relation_type']} {rel_data['theorem_name']}")
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 409:
                        logger.warning(f"Relation concept-théorème déjà existante: {rel_data}. Ignoré.")
                    else:
                        logger.error(f"Erreur lors de la création de la relation concept-théorème {rel_data}: {e.response.text}")
                except httpx.RequestError as e:
                    logger.error(f"Erreur réseau lors de la création de la relation concept-théorème {rel_data}: {e}")
            else:
                logger.warning(f"Concept ou théorème non trouvé pour la relation: {rel_data}. Ignoré.")

    logger.info("Peuplement de la Base de Connaissances terminé.")

if __name__ == "__main__":
    # Exécuter le peuplement de manière asynchrone
    try:
        asyncio.run(populate_kb())
    except httpx.RequestError as e:
        logger.error(f"Impossible de se connecter au service de persistance. Assurez-vous qu'il est en cours d'exécution à {PERSISTENCE_SERVICE_URL}. Erreur: {e}")
    except Exception as e:
        logger.critical(f"Une erreur inattendue est survenue lors du peuplement de la KB: {e}", exc_info=True)

