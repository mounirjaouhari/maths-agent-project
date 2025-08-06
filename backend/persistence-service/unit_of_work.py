# Fichier placeholder pour unit_of_work.py
# backend/persistence-service/unit_of_work.py

from typing import Type
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from .database import AsyncSessionLocal # Importe la fabrique de sessions
from .repository import (
    AbstractRepository,
    AbstractUserRepository, AbstractProjectRepository, AbstractDocumentRepository,
    AbstractDocumentVersionRepository, AbstractContentBlockRepository, AbstractExerciseRepository,
    AbstractWorkflowTaskRepository, AbstractUserFeedbackRepository,
    AbstractMathematicalConceptRepository, AbstractConceptDefinitionRepository,
    AbstractConceptPropertyRepository, AbstractTheoremRepository,
    AbstractPedagogicalPitfallRepository, AbstractPedagogicalAnalogyRepository,
    AbstractConceptApplicationRepository, AbstractHistoricalNoteRepository
)
from .repositories.user_repository import UserRepository
from .repositories.project_repository import ProjectRepository
from .repositories.document_repository import DocumentRepository
from .repositories.document_version_repository import DocumentVersionRepository
from .repositories.content_block_repository import ContentBlockRepository
from .repositories.exercise_repository import ExerciseRepository
from .repositories.workflow_task_repository import WorkflowTaskRepository
from .repositories.user_feedback_repository import UserFeedbackRepository
from .repositories.kb_repository import (
    MathematicalConceptRepository, ConceptDefinitionRepository,
    ConceptPropertyRepository, TheoremRepository,
    PedagogicalPitfallRepository, PedagogicalAnalogyRepository,
    ConceptApplicationRepository, HistoricalNoteRepository
)

logger = logging.getLogger(__name__)

class UnitOfWork:
    """
    Implémentation du modèle d'Unité de Travail (Unit of Work).
    Encapsule une session de base de données et fournit un accès aux dépôts,
    gérant les transactions de manière atomique.
    """
    def __init__(self):
        self.session_factory = AsyncSessionLocal # Utilise la fabrique de sessions

    async def __aenter__(self):
        """
        Méthode appelée lors de l'entrée dans le bloc 'async with'.
        Ouvre une nouvelle session et initialise les dépôts.
        """
        self.session: AsyncSession = self.session_factory()
        
        # Initialise tous les dépôts nécessaires
        self.users = UserRepository(self.session)
        self.projects = ProjectRepository(self.session)
        self.documents = DocumentRepository(self.session)
        self.document_versions = DocumentVersionRepository(self.session)
        self.content_blocks = ContentBlockRepository(self.session)
        self.exercises = ExerciseRepository(self.session)
        self.workflow_tasks = WorkflowTaskRepository(self.session)
        self.user_feedback = UserFeedbackRepository(self.session)
        
        # Dépôts de la Base de Connaissances (KB)
        self.mathematical_concepts = MathematicalConceptRepository(self.session)
        self.concept_definitions = ConceptDefinitionRepository(self.session)
        self.concept_properties = ConceptPropertyRepository(self.session)
        self.theorems = TheoremRepository(self.session)
        self.pedagogical_pitfalls = PedagogicalPitfallRepository(self.session)
        self.pedagogical_analogies = PedagogicalAnalogyRepository(self.session)
        self.concept_applications = ConceptApplicationRepository(self.session)
        self.historical_notes = HistoricalNoteRepository(self.session)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Méthode appelée lors de la sortie du bloc 'async with'.
        Gère le rollback ou le commit et ferme la session.
        """
        if exc_type: # Si une exception s'est produite
            logger.error(f"Transaction rollback due to exception: {exc_val}", exc_info=True)
            await self.rollback()
        else:
            await self.commit()
        await self.session.close()

    async def commit(self):
        """Valide la transaction."""
        try:
            await self.session.commit()
            logger.debug("Transaction committed.")
        except Exception as e:
            logger.error(f"Error during commit, attempting rollback: {e}", exc_info=True)
            await self.rollback()
            raise # Re-lève l'exception après le rollback

    async def rollback(self):
        """Annule la transaction."""
        await self.session.rollback()
        logger.warning("Transaction rolled back.")

