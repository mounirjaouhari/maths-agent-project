# backend/kb-service/api/internal/endpoints.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from shared.exceptions import NotFoundException, BadRequestException, ServiceUnavailableException, InternalServerError
from ..kb.models import (
    MathematicalConceptResponse, ConceptDefinitionResponse, PedagogicalPitfallResponse,
    PedagogicalAnalogyResponse, TheoremResponse, HistoricalNoteResponse,
    ConceptApplicationResponse
)
from ..kb.repository import (
    MathematicalConceptRepository, ConceptDefinitionRepository,
    TheoremRepository, PedagogicalPitfallRepository, PedagogicalAnalogyRepository,
    ConceptApplicationRepository, HistoricalNoteRepository
)
from shared.config import get_settings # Pour obtenir l'URL du service de persistance
from ..main import redis_client # Pour le caching

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()

# Instancier les dépôts (ils dépendront de l'URL du service de persistance)
# Dans un système réel, ces dépôts seraient injectés via un système de dépendances
concept_repo = MathematicalConceptRepository(settings.PERSISTENCE_SERVICE_URL)
definition_repo = ConceptDefinitionRepository(settings.PERSISTENCE_SERVICE_URL)
theorem_repo = TheoremRepository(settings.PERSISTENCE_SERVICE_URL)
pitfall_repo = PedagogicalPitfallRepository(settings.PERSISTENCE_SERVICE_URL)
analogy_repo = PedagogicalAnalogyRepository(settings.PERSISTENCE_SERVICE_URL)
application_repo = ConceptApplicationRepository(settings.PERSISTENCE_SERVICE_URL)
historical_note_repo = HistoricalNoteRepository(settings.PERSISTENCE_SERVICE_URL)


@router.get("/concepts/{concept_id}", response_model=MathematicalConceptResponse, summary="Obtenir les détails d'un concept mathématique par ID")
async def get_concept_by_id(concept_id: str):
    """
    Récupère les informations de base sur un concept mathématique par son ID.
    """
    try:
        concept = await concept_repo.get_by_id(UUID(concept_id))
        if not concept:
            raise NotFoundException(detail=f"Concept avec l'ID {concept_id} non trouvé.")
        return concept
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du concept {concept_id}: {e}", exc_info=True)
        raise InternalServerError(detail="Erreur interne lors de la récupération du concept.")

@router.get("/concepts/slug/{slug}", response_model=MathematicalConceptResponse, summary="Obtenir les détails d'un concept mathématique par slug")
async def get_concept_by_slug(slug: str):
    """
    Récupère les informations de base sur un concept mathématique par son slug.
    """
    try:
        # Tenter de récupérer depuis le cache Redis
        cache_key = f"kb:concept:slug:{slug}"
        if redis_client:
            cached_concept_json = await redis_client.get(cache_key)
            if cached_concept_json:
                logger.info(f"Concept '{slug}' trouvé dans le cache.")
                return MathematicalConceptResponse.model_validate_json(cached_concept_json)

        concept = await concept_repo.get_by_slug(slug)
        if not concept:
            raise NotFoundException(detail=f"Concept avec le slug '{slug}' non trouvé.")
        
        # Stocker dans le cache Redis
        if redis_client:
            await redis_client.set(cache_key, concept.model_dump_json(), ex=3600) # Cache pour 1 heure
            logger.info(f"Concept '{slug}' mis en cache.")

        return concept
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du concept par slug '{slug}': {e}", exc_info=True)
        raise InternalServerError(detail="Erreur interne lors de la récupération du concept par slug.")

@router.get("/concepts/{concept_id}/definitions", response_model=List[ConceptDefinitionResponse], summary="Obtenir les définitions pour un concept")
async def get_definitions_for_concept(
    concept_id: str,
    type: Optional[str] = None,
    level: Optional[str] = None
):
    """
    Récupère les définitions (formelles, intuitives, etc.) pour un concept donné,
    avec option de filtrage par type et niveau.
    """
    try:
        # Tenter de récupérer depuis le cache Redis
        cache_key = f"kb:concept:{concept_id}:definitions:type={type or 'any'}:level={level or 'any'}"
        if redis_client:
            cached_definitions_json = await redis_client.get(cache_key)
            if cached_definitions_json:
                logger.info(f"Définitions pour concept '{concept_id}' trouvées dans le cache.")
                return [ConceptDefinitionResponse.model_validate_json(d) for d in cached_definitions_json] # Assurez-vous que c'est une liste de JSON

        definitions = await definition_repo.list_by_concept_and_type(UUID(concept_id), type=type, level=level)
        
        if not definitions:
            logger.info(f"Aucune définition trouvée pour le concept {concept_id}.")
            return []
        
        # Stocker dans le cache Redis
        if redis_client:
            # Convertir la liste de modèles Pydantic en liste de chaînes JSON
            definitions_json_list = [d.model_dump_json() for d in definitions]
            await redis_client.set(cache_key, definitions_json_list, ex=3600) # Cache pour 1 heure
            logger.info(f"Définitions pour concept '{concept_id}' mises en cache.")

        return definitions
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des définitions pour le concept {concept_id}: {e}", exc_info=True)
        raise InternalServerError(detail="Erreur interne lors de la récupération des définitions.")

@router.get("/concepts/{concept_id}/prerequisites", response_model=List[MathematicalConceptResponse], summary="Obtenir les prérequis pour un concept")
async def get_prerequisites_for_concept(
    concept_id: str,
    recursive: bool = False
):
    """
    Récupère les concepts prérequis pour un concept donné.
    Peut être récursif pour obtenir tous les prérequis directs et indirects.
    """
    try:
        cache_key = f"kb:concept:{concept_id}:prerequisites:recursive={recursive}"
        if redis_client:
            cached_prerequisites_json = await redis_client.get(cache_key)
            if cached_prerequisites_json:
                logger.info(f"Prérequis pour concept '{concept_id}' trouvés dans le cache.")
                return [MathematicalConceptResponse.model_validate_json(p) for p in cached_prerequisites_json]

        prerequisites = await concept_repo.get_prerequisites(UUID(concept_id), recursive=recursive)
        
        if redis_client:
            prerequisites_json_list = [p.model_dump_json() for p in prerequisites]
            await redis_client.set(cache_key, prerequisites_json_list, ex=3600)

        return prerequisites
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des prérequis pour le concept {concept_id}: {e}", exc_info=True)
        raise InternalServerError(detail="Erreur interne lors de la récupération des prérequis.")

@router.get("/concepts/{concept_id}/pitfalls", response_model=List[PedagogicalPitfallResponse], summary="Obtenir les pièges pédagogiques pour un concept")
async def get_pitfalls_for_concept(
    concept_id: str,
    level: Optional[str] = None
):
    """
    Récupère les pièges pédagogiques associés à un concept, filtrés par niveau.
    """
    try:
        pitfalls = await pitfall_repo.list_by_concept(UUID(concept_id), level=level)
        return pitfalls
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des pièges pour le concept {concept_id}: {e}", exc_info=True)
        raise InternalServerError(detail="Erreur interne lors de la récupération des pièges pédagogiques.")

@router.get("/concepts/{concept_id}/analogies", response_model=List[PedagogicalAnalogyResponse], summary="Obtenir les analogies pour un concept")
async def get_analogies_for_concept(
    concept_id: str,
    level: Optional[str] = None,
    domain: Optional[str] = None
):
    """
    Récupère les analogies pour un concept, filtrées par niveau et domaine.
    """
    try:
        analogies = await analogy_repo.list_by_concept(UUID(concept_id), level=level, domain=domain)
        return analogies
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des analogies pour le concept {concept_id}: {e}", exc_info=True)
        raise InternalServerError(detail="Erreur interne lors de la récupération des analogies.")

@router.get("/concepts/{concept_id}/applications", response_model=List[ConceptApplicationResponse], summary="Obtenir les applications pour un concept")
async def get_applications_for_concept(
    concept_id: str,
    domain: Optional[str] = None
):
    """
    Récupère les applications concrètes ou les liens transdisciplinaires d'un concept.
    """
    try:
        applications = await application_repo.list_by_concept(UUID(concept_id), domain=domain)
        return applications
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des applications pour le concept {concept_id}: {e}", exc_info=True)
        raise InternalServerError(detail="Erreur interne lors de la récupération des applications.")

@router.get("/theorems/{theorem_id}", response_model=TheoremResponse, summary="Obtenir les détails d'un théorème par ID")
async def get_theorem_by_id(theorem_id: str):
    """
    Récupère les informations de base sur un théorème par son ID.
    """
    try:
        theorem = await theorem_repo.get_by_id(UUID(theorem_id))
        if not theorem:
            raise NotFoundException(detail=f"Théorème avec l'ID {theorem_id} non trouvé.")
        return theorem
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du théorème {theorem_id}: {e}", exc_info=True)
        raise InternalServerError(detail="Erreur interne lors de la récupération du théorème.")

@router.get("/historical-notes", response_model=List[HistoricalNoteResponse], summary="Obtenir les notes historiques liées à une entité")
async def get_historical_notes_for_entity(
    entity_id: str,
    entity_type: str
):
    """
    Récupère les notes historiques associées à un concept ou un théorème.
    """
    if entity_type not in ["concept", "theorem"]:
        raise BadRequestException(detail="Le type d'entité doit être 'concept' ou 'theorem'.")
    try:
        notes = await historical_note_repo.list_by_entity(UUID(entity_id), entity_type)
        return notes
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des notes historiques pour l'entité {entity_type}/{entity_id}: {e}", exc_info=True)
        raise InternalServerError(detail="Erreur interne lors de la récupération des notes historiques.")

