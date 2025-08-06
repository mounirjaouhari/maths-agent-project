# backend/persistence-service/repositories/document_repository.py

from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..repository import AbstractDocumentRepository, AbstractRepository
from ..models import Document # Importe le modèle ORM Document
from shared.exceptions import ConflictException, NotFoundException, InternalServerError

class DocumentRepository(AbstractDocumentRepository[Document]):
    """
    Implémentation concrète du dépôt pour l'entité Document, utilisant SQLAlchemy.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(session, Document) # Initialise la classe de base avec la session et le modèle Document

    async def add(self, document: Document) -> Document:
        """
        Ajoute un nouveau document à la base de données.
        """
        try:
            self.session.add(document)
            await self.session.flush() # Flush pour obtenir l'ID si nécessaire avant commit
            await self.session.refresh(document) # Rafraîchit l'objet avec les données de la DB (ex: created_at)
            return document
        except IntegrityError as e:
            await self.session.rollback()
            raise InternalServerError(detail="Erreur d'intégrité lors de l'ajout du document.")
        except Exception as e:
            await self.session.rollback()
            raise InternalServerError(detail=f"Erreur inattendue lors de l'ajout du document: {e}")

    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        """Récupère un document par son ID."""
        result = await self.session.execute(
            select(Document).filter(Document.document_id == document_id)
        )
        return result.scalar_one_or_none()

    async def get_by_project_id(self, project_id: UUID) -> Optional[Document]:
        """Récupère un document par l'ID de son projet parent."""
        result = await self.session.execute(
            select(Document).filter(Document.project_id == project_id)
        )
        return result.scalar_one_or_none()

    async def update(self, document_id: UUID, update_data: Dict[str, Any]) -> Optional[Document]:
        """
        Met à jour un document existant par son ID.
        update_data est un dictionnaire des champs à mettre à jour.
        """
        stmt = (
            update(Document)
            .where(Document.document_id == document_id)
            .values(**update_data)
            .returning(Document) # Retourne l'objet mis à jour
        )
        result = await self.session.execute(stmt)
        updated_document = result.scalar_one_or_none()
        if not updated_document:
            raise NotFoundException(detail=f"Document avec l'ID {document_id} non trouvé pour mise à jour.")
        return updated_document
    
    async def update_current_version(self, document_id: UUID, new_version_id: UUID) -> Optional[Document]:
        """Met à jour la version courante d'un document."""
        return await self.update(document_id, {"current_version_id": new_version_id})

    async def delete(self, document_id: UUID) -> bool:
        """Supprime un document par son ID."""
        stmt = delete(Document).where(Document.document_id == document_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0 # Retourne True si au moins une ligne a été supprimée

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Document]:
        """Liste tous les documents avec pagination."""
        result = await self.session.execute(
            select(Document).offset(skip).limit(limit)
        )
        return result.scalars().all()

