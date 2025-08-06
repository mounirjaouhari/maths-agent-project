# backend/persistence-service/repositories/content_block_repository.py

from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..repository import AbstractContentBlockRepository, AbstractRepository
from ..models import ContentBlock # Importe le modèle ORM ContentBlock
from shared.exceptions import ConflictException, NotFoundException, InternalServerError

class ContentBlockRepository(AbstractContentBlockRepository[ContentBlock]):
    """
    Implémentation concrète du dépôt pour l'entité ContentBlock, utilisant SQLAlchemy.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(session, ContentBlock) # Initialise la classe de base avec la session et le modèle ContentBlock

    async def add(self, content_block: ContentBlock) -> ContentBlock:
        """
        Ajoute un nouveau bloc de contenu à la base de données.
        """
        try:
            self.session.add(content_block)
            await self.session.flush() # Flush pour obtenir l'ID si nécessaire avant commit
            await self.session.refresh(content_block) # Rafraîchit l'objet avec les données de la DB
            return content_block
        except IntegrityError as e:
            await self.session.rollback()
            raise InternalServerError(detail="Erreur d'intégrité lors de l'ajout du bloc de contenu.")
        except Exception as e:
            await self.session.rollback()
            raise InternalServerError(detail=f"Erreur inattendue lors de l'ajout du bloc de contenu: {e}")

    async def get_by_id(self, block_id: UUID) -> Optional[ContentBlock]:
        """Récupère un bloc de contenu par son ID."""
        result = await self.session.execute(
            select(ContentBlock).filter(ContentBlock.block_id == block_id)
        )
        return result.scalar_one_or_none()

    async def update(self, block_id: UUID, update_data: Dict[str, Any]) -> Optional[ContentBlock]:
        """
        Met à jour un bloc de contenu existant par son ID.
        update_data est un dictionnaire des champs à mettre à jour.
        """
        stmt = (
            update(ContentBlock)
            .where(ContentBlock.block_id == block_id)
            .values(**update_data)
            .returning(ContentBlock) # Retourne l'objet mis à jour
        )
        result = await self.session.execute(stmt)
        updated_block = result.scalar_one_or_none()
        if not updated_block:
            raise NotFoundException(detail=f"Bloc de contenu avec l'ID {block_id} non trouvé pour mise à jour.")
        return updated_block

    async def delete(self, block_id: UUID) -> bool:
        """Supprime un bloc de contenu par son ID."""
        stmt = delete(ContentBlock).where(ContentBlock.block_id == block_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0 # Retourne True si au moins une ligne a été supprimée

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[ContentBlock]:
        """Liste tous les blocs de contenu avec pagination."""
        result = await self.session.execute(
            select(ContentBlock).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def list_by_version(self, version_id: UUID, status: Optional[str] = None) -> List[ContentBlock]:
        """Liste les blocs de contenu pour une version de document, avec option de filtrage par statut."""
        query = select(ContentBlock).filter(ContentBlock.version_id == version_id)
        if status:
            query = query.filter(ContentBlock.status == status)
        
        result = await self.session.execute(query)
        return result.scalars().all()

