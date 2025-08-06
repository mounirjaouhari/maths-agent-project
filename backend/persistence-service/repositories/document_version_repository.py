# backend/persistence-service/repositories/document_version_repository.py

from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..repository import AbstractDocumentVersionRepository, AbstractRepository
from ..models import DocumentVersion # Importe le modèle ORM DocumentVersion
from shared.exceptions import ConflictException, NotFoundException, InternalServerError

class DocumentVersionRepository(AbstractDocumentVersionRepository[DocumentVersion]):
    """
    Implémentation concrète du dépôt pour l'entité DocumentVersion, utilisant SQLAlchemy.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(session, DocumentVersion) # Initialise la classe de base avec la session et le modèle DocumentVersion

    async def add(self, document_version: DocumentVersion) -> DocumentVersion:
        """
        Ajoute une nouvelle version de document à la base de données.
        """
        try:
            self.session.add(document_version)
            await self.session.flush() # Flush pour obtenir l'ID si nécessaire avant commit
            await self.session.refresh(document_version) # Rafraîchit l'objet avec les données de la DB
            return document_version
        except IntegrityError as e:
            await self.session.rollback()
            raise InternalServerError(detail="Erreur d'intégrité lors de l'ajout de la version du document.")
        except Exception as e:
            await self.session.rollback()
            raise InternalServerError(detail=f"Erreur inattendue lors de l'ajout de la version du document: {e}")

    async def get_by_id(self, version_id: UUID) -> Optional[DocumentVersion]:
        """Récupère une version de document par son ID."""
        result = await self.session.execute(
            select(DocumentVersion).filter(DocumentVersion.version_id == version_id)
        )
        return result.scalar_one_or_none()

    async def update(self, version_id: UUID, update_data: Dict[str, Any]) -> Optional[DocumentVersion]:
        """
        Met à jour une version de document existante par son ID.
        update_data est un dictionnaire des champs à mettre à jour.
        """
        stmt = (
            update(DocumentVersion)
            .where(DocumentVersion.version_id == version_id)
            .values(**update_data)
            .returning(DocumentVersion) # Retourne l'objet mis à jour
        )
        result = await self.session.execute(stmt)
        updated_version = result.scalar_one_or_none()
        if not updated_version:
            raise NotFoundException(detail=f"Version de document avec l'ID {version_id} non trouvée pour mise à jour.")
        return updated_version

    async def delete(self, version_id: UUID) -> bool:
        """Supprime une version de document par son ID."""
        stmt = delete(DocumentVersion).where(DocumentVersion.version_id == version_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0 # Retourne True si au moins une ligne a été supprimée

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[DocumentVersion]:
        """Liste toutes les versions de documents avec pagination."""
        result = await self.session.execute(
            select(DocumentVersion).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_latest_version_number(self, document_id: UUID) -> int:
        """
        Récupère le numéro de la dernière version pour un document donné.
        Retourne 0 si aucune version n'existe pour ce document.
        """
        result = await self.session.execute(
            select(func.max(DocumentVersion.version_number))
            .filter(DocumentVersion.document_id == document_id)
        )
        latest_version = result.scalar_one_or_none()
        return latest_version if latest_version is not None else 0

