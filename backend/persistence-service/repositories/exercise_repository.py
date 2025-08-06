# backend/persistence-service/repositories/exercise_repository.py

from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..repository import AbstractExerciseRepository, AbstractRepository
from ..models import Exercise # Importe le modèle ORM Exercise
from shared.exceptions import ConflictException, NotFoundException, InternalServerError

class ExerciseRepository(AbstractExerciseRepository[Exercise]):
    """
    Implémentation concrète du dépôt pour l'entité Exercise, utilisant SQLAlchemy.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(session, Exercise) # Initialise la classe de base avec la session et le modèle Exercise

    async def add(self, exercise: Exercise) -> Exercise:
        """
        Ajoute un nouvel exercice à la base de données.
        """
        try:
            self.session.add(exercise)
            await self.session.flush() # Flush pour obtenir l'ID si nécessaire avant commit
            await self.session.refresh(exercise) # Rafraîchit l'objet avec les données de la DB
            return exercise
        except IntegrityError as e:
            await self.session.rollback()
            raise InternalServerError(detail="Erreur d'intégrité lors de l'ajout de l'exercice.")
        except Exception as e:
            await self.session.rollback()
            raise InternalServerError(detail=f"Erreur inattendue lors de l'ajout de l'exercice: {e}")

    async def get_by_id(self, exercise_id: UUID) -> Optional[Exercise]:
        """Récupère un exercice par son ID."""
        result = await self.session.execute(
            select(Exercise).filter(Exercise.exercise_id == exercise_id)
        )
        return result.scalar_one_or_none()

    async def update(self, exercise_id: UUID, update_data: Dict[str, Any]) -> Optional[Exercise]:
        """
        Met à jour un exercice existant par son ID.
        update_data est un dictionnaire des champs à mettre à jour.
        """
        stmt = (
            update(Exercise)
            .where(Exercise.exercise_id == exercise_id)
            .values(**update_data)
            .returning(Exercise) # Retourne l'objet mis à jour
        )
        result = await self.session.execute(stmt)
        updated_exercise = result.scalar_one_one_or_none()
        if not updated_exercise:
            raise NotFoundException(detail=f"Exercice avec l'ID {exercise_id} non trouvé pour mise à jour.")
        return updated_exercise

    async def delete(self, exercise_id: UUID) -> bool:
        """Supprime un exercice par son ID."""
        stmt = delete(Exercise).where(Exercise.exercise_id == exercise_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0 # Retourne True si au moins une ligne a été supprimée

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Exercise]:
        """Liste tous les exercices avec pagination."""
        result = await self.session.execute(
            select(Exercise).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def list_by_version(self, version_id: UUID) -> List[Exercise]:
        """Liste les exercices pour une version de document."""
        query = select(Exercise).filter(Exercise.version_id == version_id)
        
        result = await self.session.execute(query)
        return result.scalars().all()

