# backend/persistence-service/repositories/kb_repository.py

from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..repository import (
    AbstractMathematicalConceptRepository, AbstractConceptDefinitionRepository,
    AbstractConceptPropertyRepository, AbstractTheoremRepository,
    AbstractPedagogicalPitfallRepository, AbstractPedagogicalAnalogyRepository,
    AbstractConceptApplicationRepository, AbstractHistoricalNoteRepository,
    AbstractRepository
)
from ..models import (
    MathematicalConcept, ConceptDefinition, ConceptProperty, Theorem,
    PedagogicalPitfall, PedagogicalAnalogy, ConceptApplication, HistoricalNote,
    ConceptPrerequisite, ConceptTheoremRelation # Pour les tables de jointure
)
from shared.exceptions import ConflictException, NotFoundException, InternalServerError

# --- Implémentations des dépôts pour les entités de la KB ---

class MathematicalConceptRepository(AbstractMathematicalConceptRepository[MathematicalConcept]):
    """
    Implémentation concrète du dépôt pour l'entité MathematicalConcept, utilisant SQLAlchemy.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(session, MathematicalConcept)

    async def add(self, concept: MathematicalConcept) -> MathematicalConcept:
        try:
            self.session.add(concept)
            await self.session.flush()
            await self.session.refresh(concept)
            return concept
        except IntegrityError as e:
            await self.session.rollback()
            if "mathematical_concepts_name_key" in str(e) or "mathematical_concepts_slug_key" in str(e):
                raise ConflictException(detail=f"Un concept avec ce nom ou slug existe déjà.")
            raise InternalServerError(detail="Erreur d'intégrité lors de l'ajout du concept mathématique.")
        except Exception as e:
            await self.session.rollback()
            raise InternalServerError(detail=f"Erreur inattendue lors de l'ajout du concept mathématique: {e}")

    async def get_by_id(self, concept_id: UUID) -> Optional[MathematicalConcept]:
        result = await self.session.execute(
            select(MathematicalConcept).filter(MathematicalConcept.concept_id == concept_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[MathematicalConcept]:
        result = await self.session.execute(
            select(MathematicalConcept).filter(MathematicalConcept.slug == slug)
        )
        return result.scalar_one_or_none()

    async def update(self, concept_id: UUID, update_data: Dict[str, Any]) -> Optional[MathematicalConcept]:
        stmt = (
            update(MathematicalConcept)
            .where(MathematicalConcept.concept_id == concept_id)
            .values(**update_data)
            .returning(MathematicalConcept)
        )
        result = await self.session.execute(stmt)
        updated_concept = result.scalar_one_or_none()
        if not updated_concept:
            raise NotFoundException(detail=f"Concept mathématique avec l'ID {concept_id} non trouvé pour mise à jour.")
        return updated_concept

    async def delete(self, concept_id: UUID) -> bool:
        stmt = delete(MathematicalConcept).where(MathematicalConcept.concept_id == concept_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[MathematicalConcept]:
        result = await self.session.execute(
            select(MathematicalConcept).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_prerequisites(self, concept_id: UUID, recursive: bool = False) -> List[MathematicalConcept]:
        """
        Récupère les prérequis d'un concept.
        Si recursive est True, récupère tous les prérequis directs et indirects.
        Implémentation avec CTE récursive pour PostgreSQL.
        """
        if not recursive:
            query = select(MathematicalConcept).join(
                ConceptPrerequisite,
                MathematicalConcept.concept_id == ConceptPrerequisite.prerequisite_concept_id
            ).filter(ConceptPrerequisite.concept_id == concept_id)
            result = await self.session.execute(query)
            return result.scalars().all()
        else:
            # Implémentation de CTE récursive pour les prérequis
            # Ceci est un exemple simplifié et peut nécessiter des ajustements
            # pour des requêtes complexes ou des performances optimisées.
            from sqlalchemy import text
            recursive_cte = text(f"""
                WITH RECURSIVE concept_prerequisites_recursive (concept_id, prerequisite_concept_id, depth) AS (
                    SELECT cp.concept_id, cp.prerequisite_concept_id, 1
                    FROM concept_prerequisites cp
                    WHERE cp.concept_id = '{concept_id}'
                    UNION ALL
                    SELECT cpr.concept_id, cp.prerequisite_concept_id, cpr.depth + 1
                    FROM concept_prerequisites_recursive cpr
                    JOIN concept_prerequisites cp ON cpr.prerequisite_concept_id = cp.concept_id
                )
                SELECT mc.* FROM mathematical_concepts mc
                JOIN concept_prerequisites_recursive cpr ON mc.concept_id = cpr.prerequisite_concept_id
                WHERE mc.concept_id != '{concept_id}';
            """)
            result = await self.session.execute(recursive_cte)
            return [MathematicalConcept(**row._asdict()) for row in result.all()]


class ConceptDefinitionRepository(AbstractConceptDefinitionRepository[ConceptDefinition]):
    """
    Implémentation concrète du dépôt pour l'entité ConceptDefinition.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(session, ConceptDefinition)

    async def add(self, definition: ConceptDefinition) -> ConceptDefinition:
        try:
            self.session.add(definition)
            await self.session.flush()
            await self.session.refresh(definition)
            return definition
        except IntegrityError as e:
            await self.session.rollback()
            raise InternalServerError(detail="Erreur d'intégrité lors de l'ajout de la définition de concept.")
        except Exception as e:
            await self.session.rollback()
            raise InternalServerError(detail=f"Erreur inattendue lors de l'ajout de la définition de concept: {e}")

    async def get_by_id(self, definition_id: UUID) -> Optional[ConceptDefinition]:
        result = await self.session.execute(
            select(ConceptDefinition).filter(ConceptDefinition.definition_id == definition_id)
        )
        return result.scalar_one_or_none()

    async def update(self, definition_id: UUID, update_data: Dict[str, Any]) -> Optional[ConceptDefinition]:
        stmt = (
            update(ConceptDefinition)
            .where(ConceptDefinition.definition_id == definition_id)
            .values(**update_data)
            .returning(ConceptDefinition)
        )
        result = await self.session.execute(stmt)
        updated_definition = result.scalar_one_or_none()
        if not updated_definition:
            raise NotFoundException(detail=f"Définition de concept avec l'ID {definition_id} non trouvée pour mise à jour.")
        return updated_definition

    async def delete(self, definition_id: UUID) -> bool:
        stmt = delete(ConceptDefinition).where(ConceptDefinition.definition_id == definition_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[ConceptDefinition]:
        result = await self.session.execute(
            select(ConceptDefinition).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def list_by_concept_and_type(self, concept_id: UUID, type: Optional[str] = None, level: Optional[str] = None) -> List[ConceptDefinition]:
        query = select(ConceptDefinition).filter(ConceptDefinition.concept_id == concept_id)
        if type:
            query = query.filter(ConceptDefinition.type == type)
        if level:
            query = query.filter(ConceptDefinition.level == level)
        result = await self.session.execute(query)
        return result.scalars().all()


class ConceptPropertyRepository(AbstractRepository[ConceptProperty]):
    """
    Implémentation concrète du dépôt pour l'entité ConceptProperty.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(session, ConceptProperty)

    async def add(self, prop: ConceptProperty) -> ConceptProperty:
        try:
            self.session.add(prop)
            await self.session.flush()
            await self.session.refresh(prop)
            return prop
        except IntegrityError as e:
            await self.session.rollback()
            raise InternalServerError(detail="Erreur d'intégrité lors de l'ajout de la propriété de concept.")
        except Exception as e:
            await self.session.rollback()
            raise InternalServerError(detail=f"Erreur inattendue lors de l'ajout de la propriété de concept: {e}")

    async def get_by_id(self, property_id: UUID) -> Optional[ConceptProperty]:
        result = await self.session.execute(
            select(ConceptProperty).filter(ConceptProperty.property_id == property_id)
        )
        return result.scalar_one_or_none()

    async def update(self, property_id: UUID, update_data: Dict[str, Any]) -> Optional[ConceptProperty]:
        stmt = (
            update(ConceptProperty)
            .where(ConceptProperty.property_id == property_id)
            .values(**update_data)
            .returning(ConceptProperty)
        )
        result = await self.session.execute(stmt)
        updated_prop = result.scalar_one_or_none()
        if not updated_prop:
            raise NotFoundException(detail=f"Propriété de concept avec l'ID {property_id} non trouvée pour mise à jour.")
        return updated_prop

    async def delete(self, property_id: UUID) -> bool:
        stmt = delete(ConceptProperty).where(ConceptProperty.property_id == property_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[ConceptProperty]:
        result = await self.session.execute(
            select(ConceptProperty).offset(skip).limit(limit)
        )
        return result.scalars().all()


class TheoremRepository(AbstractTheoremRepository[Theorem]):
    """
    Implémentation concrète du dépôt pour l'entité Theorem.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(session, Theorem)

    async def add(self, theorem: Theorem) -> Theorem:
        try:
            self.session.add(theorem)
            await self.session.flush()
            await self.session.refresh(theorem)
            return theorem
        except IntegrityError as e:
            await self.session.rollback()
            raise InternalServerError(detail="Erreur d'intégrité lors de l'ajout du théorème.")
        except Exception as e:
            await self.session.rollback()
            raise InternalServerError(detail=f"Erreur inattendue lors de l'ajout du théorème: {e}")

    async def get_by_id(self, theorem_id: UUID) -> Optional[Theorem]:
        result = await self.session.execute(
            select(Theorem).filter(Theorem.theorem_id == theorem_id)
        )
        return result.scalar_one_or_none()

    async def update(self, theorem_id: UUID, update_data: Dict[str, Any]) -> Optional[Theorem]:
        stmt = (
            update(Theorem)
            .where(Theorem.theorem_id == theorem_id)
            .values(**update_data)
            .returning(Theorem)
        )
        result = await self.session.execute(stmt)
        updated_theorem = result.scalar_one_or_none()
        if not updated_theorem:
            raise NotFoundException(detail=f"Théorème avec l'ID {theorem_id} non trouvé pour mise à jour.")
        return updated_theorem

    async def delete(self, theorem_id: UUID) -> bool:
        stmt = delete(Theorem).where(Theorem.theorem_id == theorem_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Theorem]:
        result = await self.session.execute(
            select(Theorem).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def list_by_concept_relation(self, concept_id: UUID, relation_type: Optional[str] = None) -> List[Theorem]:
        """
        Liste les théorèmes liés à un concept par un type de relation.
        """
        query = select(Theorem).join(
            ConceptTheoremRelation,
            Theorem.theorem_id == ConceptTheoremRelation.theorem_id
        ).filter(ConceptTheoremRelation.concept_id == concept_id)
        if relation_type:
            query = query.filter(ConceptTheoremRelation.relation_type == relation_type)
        
        result = await self.session.execute(query)
        return result.scalars().all()


class PedagogicalPitfallRepository(AbstractRepository[PedagogicalPitfall]):
    """
    Implémentation concrète du dépôt pour l'entité PedagogicalPitfall.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(session, PedagogicalPitfall)

    async def add(self, pitfall: PedagogicalPitfall) -> PedagogicalPitfall:
        try:
            self.session.add(pitfall)
            await self.session.flush()
            await self.session.refresh(pitfall)
            return pitfall
        except IntegrityError as e:
            await self.session.rollback()
            raise InternalServerError(detail="Erreur d'intégrité lors de l'ajout du piège pédagogique.")
        except Exception as e:
            await self.session.rollback()
            raise InternalServerError(detail=f"Erreur inattendue lors de l'ajout du piège pédagogique: {e}")

    async def get_by_id(self, pitfall_id: UUID) -> Optional[PedagogicalPitfall]:
        result = await self.session.execute(
            select(PedagogicalPitfall).filter(PedagogicalPitfall.pitfall_id == pitfall_id)
        )
        return result.scalar_one_or_none()

    async def update(self, pitfall_id: UUID, update_data: Dict[str, Any]) -> Optional[PedagogicalPitfall]:
        stmt = (
            update(PedagogicalPitfall)
            .where(PedagogicalPitfall.pitfall_id == pitfall_id)
            .values(**update_data)
            .returning(PedagogicalPitfall)
        )
        result = await self.session.execute(stmt)
        updated_pitfall = result.scalar_one_or_none()
        if not updated_pitfall:
            raise NotFoundException(detail=f"Piège pédagogique avec l'ID {pitfall_id} non trouvé pour mise à jour.")
        return updated_pitfall

    async def delete(self, pitfall_id: UUID) -> bool:
        stmt = delete(PedagogicalPitfall).where(PedagogicalPitfall.pitfall_id == pitfall_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[PedagogicalPitfall]:
        result = await self.session.execute(
            select(PedagogicalPitfall).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def list_by_concept(self, concept_id: UUID, level: Optional[str] = None) -> List[PedagogicalPitfall]:
        query = select(PedagogicalPitfall).filter(PedagogicalPitfall.concept_id == concept_id)
        if level:
            query = query.filter(PedagogicalPitfall.level == level)
        result = await self.session.execute(query)
        return result.scalars().all()


class PedagogicalAnalogyRepository(AbstractRepository[PedagogicalAnalogy]):
    """
    Implémentation concrète du dépôt pour l'entité PedagogicalAnalogy.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(session, PedagogicalAnalogy)

    async def add(self, analogy: PedagogicalAnalogy) -> PedagogicalAnalogy:
        try:
            self.session.add(analogy)
            await self.session.flush()
            await self.session.refresh(analogy)
            return analogy
        except IntegrityError as e:
            await self.session.rollback()
            raise InternalServerError(detail="Erreur d'intégrité lors de l'ajout de l'analogie pédagogique.")
        except Exception as e:
            await self.session.rollback()
            raise InternalServerError(detail=f"Erreur inattendue lors de l'ajout de l'analogie pédagogique: {e}")

    async def get_by_id(self, analogy_id: UUID) -> Optional[PedagogicalAnalogy]:
        result = await self.session.execute(
            select(PedagogicalAnalogy).filter(PedagogicalAnalogy.analogy_id == analogy_id)
        )
        return result.scalar_one_or_none()

    async def update(self, analogy_id: UUID, update_data: Dict[str, Any]) -> Optional[PedagogicalAnalogy]:
        stmt = (
            update(PedagogicalAnalogy)
            .where(PedagogicalAnalogy.analogy_id == analogy_id)
            .values(**update_data)
            .returning(PedagogicalAnalogy)
        )
        result = await self.session.execute(stmt)
        updated_analogy = result.scalar_one_or_none()
        if not updated_analogy:
            raise NotFoundException(detail=f"Analogie pédagogique avec l'ID {analogy_id} non trouvée pour mise à jour.")
        return updated_analogy

    async def delete(self, analogy_id: UUID) -> bool:
        stmt = delete(PedagogicalAnalogy).where(PedagogicalAnalogy.analogy_id == analogy_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[PedagogicalAnalogy]:
        result = await self.session.execute(
            select(PedagogicalAnalogy).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def list_by_concept(self, concept_id: UUID, level: Optional[str] = None, domain: Optional[str] = None) -> List[PedagogicalAnalogy]:
        query = select(PedagogicalAnalogy).filter(PedagogicalAnalogy.concept_id == concept_id)
        if level:
            query = query.filter(PedagogicalAnalogy.level == level)
        if domain:
            query = query.filter(PedagogicalAnalogy.domain == domain)
        result = await self.session.execute(query)
        return result.scalars().all()


class ConceptApplicationRepository(AbstractRepository[ConceptApplication]):
    """
    Implémentation concrète du dépôt pour l'entité ConceptApplication.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(session, ConceptApplication)

    async def add(self, application: ConceptApplication) -> ConceptApplication:
        try:
            self.session.add(application)
            await self.session.flush()
            await self.session.refresh(application)
            return application
        except IntegrityError as e:
            await self.session.rollback()
            raise InternalServerError(detail="Erreur d'intégrité lors de l'ajout de l'application de concept.")
        except Exception as e:
            await self.session.rollback()
            raise InternalServerError(detail=f"Erreur inattendue lors de l'ajout de l'application de concept: {e}")

    async def get_by_id(self, application_id: UUID) -> Optional[ConceptApplication]:
        result = await self.session.execute(
            select(ConceptApplication).filter(ConceptApplication.application_id == application_id)
        )
        return result.scalar_one_or_none()

    async def update(self, application_id: UUID, update_data: Dict[str, Any]) -> Optional[ConceptApplication]:
        stmt = (
            update(ConceptApplication)
            .where(ConceptApplication.application_id == application_id)
            .values(**update_data)
            .returning(ConceptApplication)
        )
        result = await self.session.execute(stmt)
        updated_application = result.scalar_one_or_none()
        if not updated_application:
            raise NotFoundException(detail=f"Application de concept avec l'ID {application_id} non trouvée pour mise à jour.")
        return updated_application

    async def delete(self, application_id: UUID) -> bool:
        stmt = delete(ConceptApplication).where(ConceptApplication.application_id == application_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[ConceptApplication]:
        result = await self.session.execute(
            select(ConceptApplication).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def list_by_concept(self, concept_id: UUID, domain: Optional[str] = None) -> List[ConceptApplication]:
        query = select(ConceptApplication).filter(ConceptApplication.concept_id == concept_id)
        if domain:
            query = query.filter(ConceptApplication.domain == domain)
        result = await self.session.execute(query)
        return result.scalars().all()


class HistoricalNoteRepository(AbstractRepository[HistoricalNote]):
    """
    Implémentation concrète du dépôt pour l'entité HistoricalNote.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(session, HistoricalNote)

    async def add(self, note: HistoricalNote) -> HistoricalNote:
        try:
            self.session.add(note)
            await self.session.flush()
            await self.session.refresh(note)
            return note
        except IntegrityError as e:
            await self.session.rollback()
            raise InternalServerError(detail="Erreur d'intégrité lors de l'ajout de la note historique.")
        except Exception as e:
            await self.session.rollback()
            raise InternalServerError(detail=f"Erreur inattendue lors de l'ajout de la note historique: {e}")

    async def get_by_id(self, note_id: UUID) -> Optional[HistoricalNote]:
        result = await self.session.execute(
            select(HistoricalNote).filter(HistoricalNote.note_id == note_id)
        )
        return result.scalar_one_or_none()

    async def update(self, note_id: UUID, update_data: Dict[str, Any]) -> Optional[HistoricalNote]:
        stmt = (
            update(HistoricalNote)
            .where(HistoricalNote.note_id == note_id)
            .values(**update_data)
            .returning(HistoricalNote)
        )
        result = await self.session.execute(stmt)
        updated_note = result.scalar_one_or_none()
        if not updated_note:
            raise NotFoundException(detail=f"Note historique avec l'ID {note_id} non trouvée pour mise à jour.")
        return updated_note

    async def delete(self, note_id: UUID) -> bool:
        stmt = delete(HistoricalNote).where(HistoricalNote.note_id == note_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[HistoricalNote]:
        result = await self.session.execute(
            select(HistoricalNote).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def list_by_entity(self, entity_id: UUID, entity_type: str) -> List[HistoricalNote]:
        """
        Liste les notes historiques liées à un concept ou un théorème.
        """
        if entity_type == "concept":
            query = select(HistoricalNote).filter(HistoricalNote.concept_id == entity_id)
        elif entity_type == "theorem":
            query = select(HistoricalNote).filter(HistoricalNote.theorem_id == entity_id)
        else:
            raise BadRequestException(detail=f"Type d'entité '{entity_type}' non supporté pour les notes historiques.")
        
        result = await self.session.execute(query)
        return result.scalars().all()

