# backend/persistence-service/repositories/user_feedback_repository.py

from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..repository import AbstractUserFeedbackRepository, AbstractRepository
from ..models import UserFeedback # Importe le modèle ORM UserFeedback
from shared.exceptions import ConflictException, NotFoundException, InternalServerError

class UserFeedbackRepository(AbstractUserFeedbackRepository[UserFeedback]):
    """
    Implémentation concrète du dépôt pour l'entité UserFeedback, utilisant SQLAlchemy.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserFeedback) # Initialise la classe de base avec la session et le modèle UserFeedback

    async def add(self, user_feedback: UserFeedback) -> UserFeedback:
        """
        Ajoute un nouveau feedback utilisateur à la base de données.
        """
        try:
            self.session.add(user_feedback)
            await self.session.flush() # Flush pour obtenir l'ID si nécessaire avant commit
            await self.session.refresh(user_feedback) # Rafraîchit l'objet avec les données de la DB
            return user_feedback
        except IntegrityError as e:
            await self.session.rollback()
            raise InternalServerError(detail="Erreur d'intégrité lors de l'ajout du feedback utilisateur.")
        except Exception as e:
            await self.session.rollback()
            raise InternalServerError(detail=f"Erreur inattendue lors de l'ajout du feedback utilisateur: {e}")

    async def get_by_id(self, feedback_id: UUID) -> Optional[UserFeedback]:
        """Récupère un feedback utilisateur par son ID."""
        result = await self.session.execute(
            select(UserFeedback).filter(UserFeedback.feedback_id == feedback_id)
        )
        return result.scalar_one_or_none()

    async def update(self, feedback_id: UUID, update_data: Dict[str, Any]) -> Optional[UserFeedback]:
        """
        Met à jour un feedback utilisateur existant par son ID.
        update_data est un dictionnaire des champs à mettre à jour.
        """
        stmt = (
            update(UserFeedback)
            .where(UserFeedback.feedback_id == feedback_id)
            .values(**update_data)
            .returning(UserFeedback) # Retourne l'objet mis à jour
        )
        result = await self.session.execute(stmt)
        updated_feedback = result.scalar_one_or_none()
        if not updated_feedback:
            raise NotFoundException(detail=f"Feedback utilisateur avec l'ID {feedback_id} non trouvé pour mise à jour.")
        return updated_feedback

    async def delete(self, feedback_id: UUID) -> bool:
        """Supprime un feedback utilisateur par son ID."""
        stmt = delete(UserFeedback).where(UserFeedback.feedback_id == feedback_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0 # Retourne True si au moins une ligne a été supprimée

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[UserFeedback]:
        """Liste tous les feedbacks utilisateurs avec pagination."""
        result = await self.session.execute(
            select(UserFeedback).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def list_by_block(self, block_id: UUID, status: Optional[str] = None) -> List[UserFeedback]:
        """Liste le feedback pour un bloc de contenu, avec option de filtrage par statut."""
        query = select(UserFeedback).filter(UserFeedback.block_id == block_id)
        if status:
            query = query.filter(UserFeedback.status == status)
        
        result = await self.session.execute(query)
        return result.scalars().all()
