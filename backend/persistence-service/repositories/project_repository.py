# Fichier placeholder pour project_repository.py
# backend/persistence-service/repositories/project_repository.py

from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..repository import AbstractProjectRepository, AbstractRepository
from ..models import Project # Importe le modèle ORM Project
from shared.exceptions import ConflictException, NotFoundException, InternalServerError

class ProjectRepository(AbstractProjectRepository[Project]):
    """
    Implémentation concrète du dépôt pour l'entité Project, utilisant SQLAlchemy.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(session, Project) # Initialise la classe de base avec la session et le modèle Project

    async def add(self, project: Project) -> Project:
        """
        Ajoute un nouveau projet à la base de données.
        """
        try:
            self.session.add(project)
            await self.session.flush() # Flush pour obtenir l'ID si nécessaire avant commit
            await self.session.refresh(project) # Rafraîchit l'objet avec les données de la DB (ex: created_at)
            return project
        except IntegrityError as e:
            await self.session.rollback()
            # Pour les projets, il n'y a pas de contrainte d'unicité sur le titre par défaut,
            # mais si une telle contrainte était ajoutée, elle serait gérée ici.
            raise InternalServerError(detail="Erreur d'intégrité lors de l'ajout du projet.")
        except Exception as e:
            await self.session.rollback()
            raise InternalServerError(detail=f"Erreur inattendue lors de l'ajout du projet: {e}")

    async def get_by_id(self, project_id: UUID) -> Optional[Project]:
        """Récupère un projet par son ID."""
        result = await self.session.execute(
            select(Project).filter(Project.project_id == project_id)
        )
        return result.scalar_one_or_none()

    async def update(self, project_id: UUID, update_data: Dict[str, Any]) -> Optional[Project]:
        """
        Met à jour un projet existant par son ID.
        update_data est un dictionnaire des champs à mettre à jour.
        """
        stmt = (
            update(Project)
            .where(Project.project_id == project_id)
            .values(**update_data)
            .returning(Project) # Retourne l'objet mis à jour
        )
        result = await self.session.execute(stmt)
        updated_project = result.scalar_one_or_none()
        if not updated_project:
            raise NotFoundException(detail=f"Projet avec l'ID {project_id} non trouvé pour mise à jour.")
        return updated_project

    async def delete(self, project_id: UUID) -> bool:
        """Supprime un projet par son ID."""
        stmt = delete(Project).where(Project.project_id == project_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0 # Retourne True si au moins une ligne a été supprimée

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """Liste tous les projets avec pagination."""
        result = await self.session.execute(
            select(Project).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def list_by_user(self, user_id: UUID, status: Optional[str] = None) -> List[Project]:
        """Liste les projets d'un utilisateur, avec option de filtrage par statut."""
        query = select(Project).filter(Project.user_id == user_id)
        if status:
            query = query.filter(Project.status == status)
        
        result = await self.session.execute(query)
        return result.scalars().all()

