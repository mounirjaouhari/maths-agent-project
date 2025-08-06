# Fichier placeholder pour user_repository.py
# backend/persistence-service/repositories/user_repository.py

from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..repository import AbstractUserRepository, AbstractRepository
from ..models import User # Importe le modèle ORM User
from shared.exceptions import ConflictException, NotFoundException, InternalServerError

class UserRepository(AbstractUserRepository[User]):
    """
    Implémentation concrète du dépôt pour l'entité User, utilisant SQLAlchemy.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(session, User) # Initialise la classe de base avec la session et le modèle User

    async def add(self, user: User) -> User:
        """
        Ajoute un nouvel utilisateur à la base de données.
        Lève ConflictException si le nom d'utilisateur existe déjà.
        """
        try:
            self.session.add(user)
            await self.session.flush() # Flush pour obtenir l'ID si nécessaire avant commit
            await self.session.refresh(user) # Rafraîchit l'objet avec les données de la DB (ex: created_at)
            return user
        except IntegrityError as e:
            await self.session.rollback()
            if "users_username_key" in str(e): # Vérifie la contrainte d'unicité sur le nom d'utilisateur
                raise ConflictException(detail=f"Le nom d'utilisateur '{user.username}' existe déjà.")
            raise InternalServerError(detail="Erreur d'intégrité lors de l'ajout de l'utilisateur.")
        except Exception as e:
            await self.session.rollback()
            raise InternalServerError(detail=f"Erreur inattendue lors de l'ajout de l'utilisateur: {e}")

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Récupère un utilisateur par son ID."""
        result = await self.session.execute(
            select(User).filter(User.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Récupère un utilisateur par son nom d'utilisateur."""
        result = await self.session.execute(
            select(User).filter(User.username == username)
        )
        return result.scalar_one_or_none()

    async def update(self, user_id: UUID, update_data: Dict[str, Any]) -> Optional[User]:
        """
        Met à jour un utilisateur existant par son ID.
        update_data est un dictionnaire des champs à mettre à jour.
        """
        stmt = (
            update(User)
            .where(User.user_id == user_id)
            .values(**update_data)
            .returning(User) # Retourne l'objet mis à jour
        )
        result = await self.session.execute(stmt)
        updated_user = result.scalar_one_or_none()
        if not updated_user:
            raise NotFoundException(detail=f"Utilisateur avec l'ID {user_id} non trouvé pour mise à jour.")
        return updated_user

    async def delete(self, user_id: UUID) -> bool:
        """Supprime un utilisateur par son ID."""
        stmt = delete(User).where(User.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0 # Retourne True si au moins une ligne a été supprimée

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Liste tous les utilisateurs avec pagination."""
        result = await self.session.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()

