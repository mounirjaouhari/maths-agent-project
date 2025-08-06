# Fichier placeholder pour repository.py
# backend/kb-service/kb/repository.py

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession # Utilisé si la KB est en PostgreSQL
# from neo4j import AsyncGraphDatabase # Utilisé si la KB est en Neo4j

# Définit un TypeVar pour le modèle de l'entité, permettant un typage générique
T = TypeVar('T')

class AbstractKBRepository(ABC, Generic[T]):
    """
    Classe abstraite de base pour tous les dépôts de la Base de Connaissances.
    Elle définit l'interface commune pour les opérations CRUD génériques.
    """
    # Pourrait prendre une session SQLAlchemy ou un driver Neo4j en fonction de l'implémentation
    def __init__(self, db_client: Any, model: type[T]):
        self.db_client = db_client # Ceci peut être une AsyncSession ou un driver Neo4j
        self.model = model

    @abstractmethod
    async def add(self, entity: T) -> T:
        """Ajoute une nouvelle entité à la KB."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """Récupère une entité de la KB par son ID."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, entity_id: UUID, update_data: Dict[str, Any]) -> Optional[T]:
        """Met à jour une entité existante dans la KB par son ID."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Supprime une entité de la KB par son ID."""
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Liste toutes les entités de la KB."""
        raise NotImplementedError

# --- Interfaces Abstraites Spécifiques aux Entités de la KB ---

class AbstractMathematicalConceptRepository(AbstractKBRepository[T]):
    """Interface abstraite pour le dépôt des concepts mathématiques de la KB."""
    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[T]:
        """Récupère un concept par son slug."""
        raise NotImplementedError
    
    @abstractmethod
    async def get_prerequisites(self, concept_id: UUID, recursive: bool = False) -> List[T]:
        """Récupère les prérequis d'un concept (directs ou récursifs)."""
        raise NotImplementedError

class AbstractConceptDefinitionRepository(AbstractKBRepository[T]):
    """Interface abstraite pour le dépôt des définitions de concepts de la KB."""
    @abstractmethod
    async def list_by_concept_and_type(self, concept_id: UUID, type: Optional[str] = None, level: Optional[str] = None) -> List[T]:
        """Liste les définitions pour un concept, filtrées par type et niveau."""
        raise NotImplementedError

class AbstractConceptPropertyRepository(AbstractKBRepository[T]):
    """Interface abstraite pour le dépôt des propriétés de concepts de la KB."""
    @abstractmethod
    async def list_by_concept(self, concept_id: UUID) -> List[T]:
        """Liste les propriétés pour un concept."""
        raise NotImplementedError

class AbstractTheoremRepository(AbstractKBRepository[T]):
    """Interface abstraite pour le dépôt des théorèmes de la KB."""
    @abstractmethod
    async def list_by_concept_relation(self, concept_id: UUID, relation_type: Optional[str] = None) -> List[T]:
        """Liste les théorèmes liés à un concept par un type de relation."""
        raise NotImplementedError

class AbstractPedagogicalPitfallRepository(AbstractKBRepository[T]):
    """Interface abstraite pour le dépôt des pièges pédagogiques de la KB."""
    @abstractmethod
    async def list_by_concept(self, concept_id: UUID, level: Optional[str] = None) -> List[T]:
        """Liste les pièges pédagogiques pour un concept, filtrés par niveau."""
        raise NotImplementedError

class AbstractPedagogicalAnalogyRepository(AbstractKBRepository[T]):
    """Interface abstraite pour le dépôt des analogies pédagogiques de la KB."""
    @abstractmethod
    async def list_by_concept(self, concept_id: UUID, level: Optional[str] = None, domain: Optional[str] = None) -> List[T]:
        """Liste les analogies pour un concept, filtrées par niveau et domaine."""
        raise NotImplementedError

class AbstractConceptApplicationRepository(AbstractKBRepository[T]):
    """Interface abstraite pour le dépôt des applications de concepts de la KB."""
    @abstractmethod
    async def list_by_concept(self, concept_id: UUID, domain: Optional[str] = None) -> List[T]:
        """Liste les applications pour un concept, filtrées par domaine."""
        raise NotImplementedError

class AbstractHistoricalNoteRepository(AbstractKBRepository[T]):
    """Interface abstraite pour le dépôt des notes historiques de la KB."""
    @abstractmethod
    async def list_by_entity(self, entity_id: UUID, entity_type: str) -> List[T]:
        """Liste les notes historiques liées à un concept ou un théorème."""
        raise NotImplementedError
