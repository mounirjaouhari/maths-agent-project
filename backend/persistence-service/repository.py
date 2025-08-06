# Fichier placeholder pour repository.py
# backend/persistence-service/repository.py

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Définit un TypeVar pour le modèle de l'entité, permettant une typage générique
T = TypeVar('T')

class AbstractRepository(ABC, Generic[T]):
    """
    Classe abstraite de base pour tous les dépôts.
    Elle définit l'interface commune pour les opérations CRUD génériques.
    """
    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model

    @abstractmethod
    async def add(self, entity: T) -> T:
        """Ajoute une nouvelle entité."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """Récupère une entité par son ID."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, entity_id: UUID, update_data: Dict[str, Any]) -> Optional[T]:
        """Met à jour une entité existante par son ID."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Supprime une entité par son ID."""
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Liste toutes les entités."""
        raise NotImplementedError

# --- Interfaces Abstraites Spécifiques aux Entités ---

class AbstractUserRepository(AbstractRepository[T]):
    """Interface abstraite pour le dépôt des utilisateurs."""
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[T]:
        """Récupère un utilisateur par son nom d'utilisateur."""
        raise NotImplementedError

class AbstractProjectRepository(AbstractRepository[T]):
    """Interface abstraite pour le dépôt des projets."""
    @abstractmethod
    async def list_by_user(self, user_id: UUID, status: Optional[str] = None) -> List[T]:
        """Liste les projets d'un utilisateur, avec option de filtrage par statut."""
        raise NotImplementedError

class AbstractDocumentRepository(AbstractRepository[T]):
    """Interface abstraite pour le dépôt des documents."""
    @abstractmethod
    async def get_by_project_id(self, project_id: UUID) -> Optional[T]:
        """Récupère un document par l'ID de son projet parent."""
        raise NotImplementedError
    
    @abstractmethod
    async def update_current_version(self, document_id: UUID, new_version_id: UUID) -> Optional[T]:
        """Met à jour la version courante d'un document."""
        raise NotImplementedError

class AbstractDocumentVersionRepository(AbstractRepository[T]):
    """Interface abstraite pour le dépôt des versions de documents."""
    @abstractmethod
    async def get_latest_version_number(self, document_id: UUID) -> int:
        """Récupère le numéro de la dernière version pour un document."""
        raise NotImplementedError

class AbstractContentBlockRepository(AbstractRepository[T]):
    """Interface abstraite pour le dépôt des blocs de contenu."""
    @abstractmethod
    async def list_by_version(self, version_id: UUID, status: Optional[str] = None) -> List[T]:
        """Liste les blocs de contenu pour une version de document, avec option de filtrage par statut."""
        raise NotImplementedError

class AbstractExerciseRepository(AbstractRepository[T]):
    """Interface abstraite pour le dépôt des exercices."""
    @abstractmethod
    async def list_by_version(self, version_id: UUID) -> List[T]:
        """Liste les exercices pour une version de document."""
        raise NotImplementedError

class AbstractWorkflowTaskRepository(AbstractRepository[T]):
    """Interface abstraite pour le dépôt des tâches de workflow."""
    @abstractmethod
    async def list_by_project(self, project_id: UUID, status: Optional[str] = None) -> List[T]:
        """Liste les tâches de workflow pour un projet, avec option de filtrage par statut."""
        raise NotImplementedError

class AbstractUserFeedbackRepository(AbstractRepository[T]):
    """Interface abstraite pour le dépôt du feedback utilisateur."""
    @abstractmethod
    async def list_by_block(self, block_id: UUID, status: Optional[str] = None) -> List[T]:
        """Liste le feedback pour un bloc de contenu, avec option de filtrage par statut."""
        raise NotImplementedError

# --- Interfaces Abstraites pour la Base de Connaissances (KB) ---

class AbstractMathematicalConceptRepository(AbstractRepository[T]):
    """Interface abstraite pour le dépôt des concepts mathématiques de la KB."""
    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[T]:
        """Récupère un concept par son slug."""
        raise NotImplementedError
    
    @abstractmethod
    async def get_prerequisites(self, concept_id: UUID, recursive: bool = False) -> List[T]:
        """Récupère les prérequis d'un concept (directs ou récursifs)."""
        raise NotImplementedError

class AbstractConceptDefinitionRepository(AbstractRepository[T]):
    """Interface abstraite pour le dépôt des définitions de concepts de la KB."""
    @abstractmethod
    async def list_by_concept_and_type(self, concept_id: UUID, type: Optional[str] = None, level: Optional[str] = None) -> List[T]:
        """Liste les définitions pour un concept, filtrées par type et niveau."""
        raise NotImplementedError

class AbstractTheoremRepository(AbstractRepository[T]):
    """Interface abstraite pour le dépôt des théorèmes de la KB."""
    @abstractmethod
    async def list_by_concept_relation(self, concept_id: UUID, relation_type: Optional[str] = None) -> List[T]:
        """Liste les théorèmes liés à un concept par un type de relation."""
        raise NotImplementedError

class AbstractPedagogicalPitfallRepository(AbstractRepository[T]):
    """Interface abstraite pour le dépôt des pièges pédagogiques de la KB."""
    @abstractmethod
    async def list_by_concept(self, concept_id: UUID, level: Optional[str] = None) -> List[T]:
        """Liste les pièges pédagogiques pour un concept, filtrés par niveau."""
        raise NotImplementedError

class AbstractPedagogicalAnalogyRepository(AbstractRepository[T]):
    """Interface abstraite pour le dépôt des analogies pédagogiques de la KB."""
    @abstractmethod
    async def list_by_concept(self, concept_id: UUID, level: Optional[str] = None, domain: Optional[str] = None) -> List[T]:
        """Liste les analogies pour un concept, filtrées par niveau et domaine."""
        raise NotImplementedError

class AbstractConceptApplicationRepository(AbstractRepository[T]):
    """Interface abstraite pour le dépôt des applications de concepts de la KB."""
    @abstractmethod
    async def list_by_concept(self, concept_id: UUID, domain: Optional[str] = None) -> List[T]:
        """Liste les applications pour un concept, filtrées par domaine."""
        raise NotImplementedError

class AbstractHistoricalNoteRepository(AbstractRepository[T]):
    """Interface abstraite pour le dépôt des notes historiques de la KB."""
    @abstractmethod
    async def list_by_entity(self, entity_id: UUID, entity_type: str) -> List[T]:
        """Liste les notes historiques liées à un concept ou un théorème."""
        raise NotImplementedError
