# backend/persistence-service/repositories/workflow_task_repository.py

from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..repository import AbstractWorkflowTaskRepository, AbstractRepository
from ..models import WorkflowTask # Importe le modèle ORM WorkflowTask
from shared.exceptions import ConflictException, NotFoundException, InternalServerError

class WorkflowTaskRepository(AbstractWorkflowTaskRepository[WorkflowTask]):
    """
    Implémentation concrète du dépôt pour l'entité WorkflowTask, utilisant SQLAlchemy.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(session, WorkflowTask) # Initialise la classe de base avec la session et le modèle WorkflowTask

    async def add(self, workflow_task: WorkflowTask) -> WorkflowTask:
        """
        Ajoute une nouvelle tâche de workflow à la base de données.
        """
        try:
            self.session.add(workflow_task)
            await self.session.flush() # Flush pour obtenir l'ID si nécessaire avant commit
            await self.session.refresh(workflow_task) # Rafraîchit l'objet avec les données de la DB
            return workflow_task
        except IntegrityError as e:
            await self.session.rollback()
            raise InternalServerError(detail="Erreur d'intégrité lors de l'ajout de la tâche de workflow.")
        except Exception as e:
            await self.session.rollback()
            raise InternalServerError(detail=f"Erreur inattendue lors de l'ajout de la tâche de workflow: {e}")

    async def get_by_id(self, task_id: UUID) -> Optional[WorkflowTask]:
        """Récupère une tâche de workflow par son ID."""
        result = await self.session.execute(
            select(WorkflowTask).filter(WorkflowTask.task_id == task_id)
        )
        return result.scalar_one_or_none()

    async def update(self, task_id: UUID, update_data: Dict[str, Any]) -> Optional[WorkflowTask]:
        """
        Met à jour une tâche de workflow existante par son ID.
        update_data est un dictionnaire des champs à mettre à jour.
        """
        stmt = (
            update(WorkflowTask)
            .where(WorkflowTask.task_id == task_id)
            .values(**update_data)
            .returning(WorkflowTask) # Retourne l'objet mis à jour
        )
        result = await self.session.execute(stmt)
        updated_task = result.scalar_one_or_none()
        if not updated_task:
            raise NotFoundException(detail=f"Tâche de workflow avec l'ID {task_id} non trouvée pour mise à jour.")
        return updated_task

    async def delete(self, task_id: UUID) -> bool:
        """Supprime une tâche de workflow par son ID."""
        stmt = delete(WorkflowTask).where(WorkflowTask.task_id == task_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0 # Retourne True si au moins une ligne a été supprimée

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[WorkflowTask]:
        """Liste toutes les tâches de workflow avec pagination."""
        result = await self.session.execute(
            select(WorkflowTask).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def list_by_project(self, project_id: UUID, status: Optional[str] = None) -> List[WorkflowTask]:
        """Liste les tâches de workflow pour un projet, avec option de filtrage par statut."""
        query = select(WorkflowTask).filter(WorkflowTask.project_id == project_id)
        if status:
            query = query.filter(WorkflowTask.status == status)
        
        result = await self.session.execute(query)
        return result.scalars().all()

