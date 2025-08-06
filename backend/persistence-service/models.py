# Fichier placeholder pour models.py
# backend/persistence-service/models.py

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from .database import Base # Importe la base déclarative de database.py
from shared.utils import get_current_utc_timestamp # Pour les horodatages automatiques

# --- Modèles de Données Principaux (Projet/Utilisateur) ---

class User(Base):
    """Modèle ORM pour la table 'users'."""
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, onupdate=get_current_utc_timestamp, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(String, default="user", nullable=False)

    projects = relationship("Project", back_populates="owner")
    user_feedback = relationship("UserFeedback", back_populates="user")


class Project(Base):
    """Modèle ORM pour la table 'projects'."""
    __tablename__ = "projects"

    project_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    title = Column(String, index=True, nullable=False)
    subject = Column(String, nullable=False)
    level = Column(String, nullable=False)
    style = Column(String, nullable=False)
    mode = Column(String, nullable=False) # Supervisé ou Autonome
    created_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, onupdate=get_current_utc_timestamp, nullable=False)
    status = Column(String, default="draft", nullable=False) # draft, in_progress, completed, archived
    current_step = Column(String, nullable=True) # Étape actuelle du workflow (pour mode Supervisé)

    owner = relationship("User", back_populates="projects")
    documents = relationship("Document", back_populates="project")
    workflow_tasks = relationship("WorkflowTask", back_populates="project")


class Document(Base):
    """Modèle ORM pour la table 'documents'."""
    __tablename__ = "documents"

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=False)
    # current_version_id est une FK vers document_versions, mais gérée comme une relation
    current_version_id = Column(UUID(as_uuid=True), nullable=True) # ID de la version actuellement active/principale

    created_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, onupdate=get_current_utc_timestamp, nullable=False)

    project = relationship("Project", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document")
    # Relation pour current_version (chargement paresseux par ID)
    # current_version = relationship("DocumentVersion", foreign_keys=[current_version_id], post_load=True, lazy="joined")


class DocumentVersion(Base):
    """Modèle ORM pour la table 'document_versions'."""
    __tablename__ = "document_versions"

    version_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, nullable=False)
    status = Column(String, default="draft", nullable=False) # draft, validated, archived
    content_structure = Column(JSONB, nullable=False) # Représentation structurée du document (arborescence Chapitres/Sections/Sous-sections)

    document = relationship("Document", back_populates="versions")
    content_blocks = relationship("ContentBlock", back_populates="document_version")
    exercises = relationship("Exercise", back_populates="document_version")


class ContentBlock(Base):
    """Modèle ORM pour la table 'content_blocks'."""
    __tablename__ = "content_blocks"

    block_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID(as_uuid=True), ForeignKey("document_versions.version_id"), nullable=False)
    block_type = Column(String, nullable=False) # definition, intuition, proof_skeleton, exercise, text, image, etc.
    content_latex = Column(Text, nullable=False) # Le contenu principal du bloc en format LaTeX
    content_html = Column(Text, nullable=True) # Une version rendue en HTML (pour l'affichage UI rapide)
    source_llm = Column(String, nullable=True) # Le LLM utilisé pour générer ce bloc
    generation_params = Column(JSONB, nullable=True) # Paramètres du prompt et de la génération
    qc_report = Column(JSONB, nullable=True) # Dernier rapport QC pour ce bloc
    status = Column(String, default="draft", nullable=False) # draft, qc_pending, qc_failed, validated, needs_refinement, generation_failed, refinement_failed
    created_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, onupdate=get_current_utc_timestamp, nullable=False)
    refinement_attempts = Column(Integer, default=0, nullable=False) # Nombre de tentatives de raffinement
    error_message = Column(Text, nullable=True) # Message d'erreur si le bloc est en état d'échec

    document_version = relationship("DocumentVersion", back_populates="content_blocks")
    user_feedback = relationship("UserFeedback", back_populates="content_block")
    exercises = relationship("Exercise", back_populates="content_block") # Si un exercice est directement lié à un bloc


class Exercise(Base):
    """Modèle ORM pour la table 'exercises'."""
    __tablename__ = "exercises"

    exercise_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID(as_uuid=True), ForeignKey("document_versions.version_id"), nullable=False)
    block_id = Column(UUID(as_uuid=True), ForeignKey("content_blocks.block_id"), nullable=True) # Le bloc de contenu qui contient ou référence cet exercice
    prompt_latex = Column(Text, nullable=False) # L'énoncé de l'exercice en LaTeX
    solution_latex = Column(Text, nullable=True) # La solution de l'exercice en LaTeX
    difficulty = Column(String, nullable=False) # easy, medium, hard
    exercise_type = Column(String, nullable=False) # calculation, proof, application
    source_llm = Column(String, nullable=True)
    qc_report = Column(JSONB, nullable=True)
    status = Column(String, default="draft", nullable=False) # draft, validated, needs_refinement
    created_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, onupdate=get_current_utc_timestamp, nullable=False)

    document_version = relationship("DocumentVersion", back_populates="exercises")
    content_block = relationship("ContentBlock", back_populates="exercises")


class WorkflowTask(Base):
    """Modèle ORM pour la table 'workflow_tasks'."""
    __tablename__ = "workflow_tasks"

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=False)
    task_type = Column(String, nullable=False) # generate_block, run_qc, refine_block, assemble_document, export_document
    status = Column(String, default="pending", nullable=False) # pending, in_progress, completed, failed, retrying
    parameters = Column(JSONB, nullable=False) # Paramètres spécifiques à la tâche (ex: {block_id: ..., type: 'definition'})
    celery_task_id = Column(String, nullable=True) # ID de la tâche dans Celery
    created_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, onupdate=get_current_utc_timestamp, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    project = relationship("Project", back_populates="workflow_tasks")


class UserFeedback(Base):
    """Modèle ORM pour la table 'user_feedback'."""
    __tablename__ = "user_feedback"

    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    block_id = Column(UUID(as_uuid=True), ForeignKey("content_blocks.block_id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    feedback_text = Column(Text, nullable=False)
    feedback_type = Column(String, nullable=False) # clarity, math_error, style, suggestion
    location = Column(JSONB, nullable=True) # Position ou plage de texte concernée
    created_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, nullable=False)
    status = Column(String, default="pending", nullable=False) # pending, addressed, ignored

    content_block = relationship("ContentBlock", back_populates="user_feedback")
    user = relationship("User", back_populates="user_feedback")


# --- Modèles de Données pour la Base de Connaissances (KB) ---
# Ces modèles sont pour l'implémentation de la KB en PostgreSQL avancé.

class MathematicalConcept(Base):
    """Modèle ORM pour la table 'mathematical_concepts' de la KB."""
    __tablename__ = "mathematical_concepts"

    concept_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, index=True, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    domain = Column(String, nullable=False)
    level_min = Column(String, nullable=False)
    level_max = Column(String, nullable=True)
    description_short = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, onupdate=get_current_utc_timestamp, nullable=False)

    definitions = relationship("ConceptDefinition", back_populates="concept")
    properties = relationship("ConceptProperty", back_populates="concept")
    pitfalls = relationship("PedagogicalPitfall", back_populates="concept")
    analogies = relationship("PedagogicalAnalogy", back_populates="concept")
    applications = relationship("ConceptApplication", back_populates="concept")
    historical_notes_concept = relationship("HistoricalNote", foreign_keys="[HistoricalNote.concept_id]", back_populates="concept")
    
    # Relations many-to-many via tables de jointure
    prerequisites = relationship(
        "MathematicalConcept",
        secondary="concept_prerequisites",
        primaryjoin="MathematicalConcept.concept_id == ConceptPrerequisite.concept_id",
        secondaryjoin="MathematicalConcept.concept_id == ConceptPrerequisite.prerequisite_concept_id",
        backref="required_by",
        lazy="dynamic"
    )
    theorems_related = relationship(
        "Theorem",
        secondary="concept_theorem_relation",
        back_populates="concepts_related",
        lazy="dynamic"
    )


class ConceptDefinition(Base):
    """Modèle ORM pour la table 'concept_definitions' de la KB."""
    __tablename__ = "concept_definitions"

    definition_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concept_id = Column(UUID(as_uuid=True), ForeignKey("mathematical_concepts.concept_id"), nullable=False)
    type = Column(String, nullable=False) # formelle, intuitive, visuelle
    level = Column(String, nullable=True)
    content_latex = Column(Text, nullable=False)
    source = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, nullable=False)

    concept = relationship("MathematicalConcept", back_populates="definitions")


class ConceptProperty(Base):
    """Modèle ORM pour la table 'concept_properties' de la KB."""
    __tablename__ = "concept_properties"

    property_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concept_id = Column(UUID(as_uuid=True), ForeignKey("mathematical_concepts.concept_id"), nullable=False)
    name = Column(String, nullable=False)
    description_latex = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, nullable=False)

    concept = relationship("MathematicalConcept", back_populates="properties")


class Theorem(Base):
    """Modèle ORM pour la table 'theorems' de la KB."""
    __tablename__ = "theorems"

    theorem_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=True)
    statement_latex = Column(Text, nullable=False)
    proof_sketch_latex = Column(Text, nullable=True)
    proof_full_latex = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, nullable=False)

    historical_notes_theorem = relationship("HistoricalNote", foreign_keys="[HistoricalNote.theorem_id]", back_populates="theorem")
    concepts_related = relationship(
        "MathematicalConcept",
        secondary="concept_theorem_relation",
        back_populates="theorems_related",
        lazy="dynamic"
    )


class PedagogicalPitfall(Base):
    """Modèle ORM pour la table 'pedagogical_pitfalls' de la KB."""
    __tablename__ = "pedagogical_pitfalls"

    pitfall_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concept_id = Column(UUID(as_uuid=True), ForeignKey("mathematical_concepts.concept_id"), nullable=False)
    description_short = Column(Text, nullable=False)
    explanation_latex = Column(Text, nullable=True)
    level = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, nullable=False)

    concept = relationship("MathematicalConcept", back_populates="pitfalls")


class PedagogicalAnalogy(Base):
    """Modèle ORM pour la table 'pedagogical_analogies' de la KB."""
    __tablename__ = "pedagogical_analogies"

    analogy_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concept_id = Column(UUID(as_uuid=True), ForeignKey("mathematical_concepts.concept_id"), nullable=False)
    title = Column(String, nullable=True)
    description_latex = Column(Text, nullable=False)
    domain = Column(String, nullable=True)
    level = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, nullable=False)

    concept = relationship("MathematicalConcept", back_populates="analogies")


class ConceptApplication(Base):
    """Modèle ORM pour la table 'concept_applications' de la KB."""
    __tablename__ = "concept_applications"

    application_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concept_id = Column(UUID(as_uuid=True), ForeignKey("mathematical_concepts.concept_id"), nullable=False)
    domain = Column(String, nullable=False)
    description_latex = Column(Text, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_current_utc_timestamp, nullable=False)

    concept = relationship("MathematicalConcept", back_populates="applications")


class HistoricalNote(Base):
    """Modèle ORM pour la table 'historical_notes' de la KB."""
    __tablename__ = "historical_notes"

    note_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_latex = Column(Text, nullable=False)
    date_start = Column(DateTime(timezone=True), nullable=True)
    date_end = Column(DateTime(timezone=True), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Clés étrangères nullables car une note peut être liée à un concept OU un théorème, ou aucun
    concept_id = Column(UUID(as_uuid=True), ForeignKey("mathematical_concepts.concept_id"), nullable=True)
    theorem_id = Column(UUID(as_uuid=True), ForeignKey("theorems.theorem_id"), nullable=True)

    concept = relationship("MathematicalConcept", foreign_keys=[concept_id], back_populates="historical_notes_concept")
    theorem = relationship("Theorem", foreign_keys=[theorem_id], back_populates="historical_notes_theorem")


# --- Tables de Jointure pour les Relations Many-to-Many de la KB ---

class ConceptPrerequisite(Base):
    """Table de jointure pour la relation de prérequis entre concepts."""
    __tablename__ = "concept_prerequisites"

    concept_id = Column(UUID(as_uuid=True), ForeignKey("mathematical_concepts.concept_id"), primary_key=True)
    prerequisite_concept_id = Column(UUID(as_uuid=True), ForeignKey("mathematical_concepts.concept_id"), primary_key=True)
    type = Column(String, default="required", nullable=False) # required, recommended


class ConceptTheoremRelation(Base):
    """Table de jointure pour la relation entre concepts et théorèmes."""
    __tablename__ = "concept_theorem_relation"

    concept_id = Column(UUID(as_uuid=True), ForeignKey("mathematical_concepts.concept_id"), primary_key=True)
    theorem_id = Column(UUID(as_uuid=True), ForeignKey("theorems.theorem_id"), primary_key=True)
    relation_type = Column(String, nullable=False) # defines, uses, is_example_of
