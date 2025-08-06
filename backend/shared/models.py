# backend/shared/models.py

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field

# --- Modèles de base pour les entités partagées ---

class UserBase(BaseModel):
    username: str
    is_active: bool = True
    role: str = "user"

class UserCreate(UserBase):
    password_hash: str # Le hash du mot de passe est passé ici pour la création interne

class UserResponse(UserBase):
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # Permet de mapper depuis des objets SQLAlchemy

class ProjectBase(BaseModel):
    title: str
    subject: str
    level: str
    style: str
    mode: str

class ProjectCreate(ProjectBase):
    user_id: UUID

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    level: Optional[str] = None
    style: Optional[str] = None
    mode: Optional[str] = None
    status: Optional[str] = None
    current_step: Optional[str] = None

class ProjectResponse(ProjectBase):
    project_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    status: str
    current_step: Optional[str] = None

    class Config:
        from_attributes = True

class DocumentBase(BaseModel):
    project_id: UUID

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    document_id: UUID
    current_version_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentVersionBase(BaseModel):
    document_id: UUID
    version_number: int
    content_structure: Dict[str, Any] # Structure JSON du document (arborescence)

class DocumentVersionCreate(DocumentVersionBase):
    pass

class DocumentVersionResponse(DocumentVersionBase):
    version_id: UUID
    created_at: datetime
    status: str

    class Config:
        from_attributes = True

class QCProblem(BaseModel):
    type: str
    severity: str
    description: str
    location: Optional[Dict[str, Any]] = None # Ex: {'line': 10, 'char_start': 5, 'char_end': 15}
    suggested_fix: Optional[str] = None

class QCReport(BaseModel):
    overall_score: float = Field(..., ge=0, le=100)
    status: str # Ex: 'passed', 'failed', 'partial_success'
    problems: List[QCProblem] = []
    details: Optional[Dict[str, Any]] = None # Détails bruts des analyses par sous-module

class ContentBlockBase(BaseModel):
    version_id: UUID
    block_type: str
    content_latex: str
    content_html: Optional[str] = None
    source_llm: Optional[str] = None
    generation_params: Optional[Dict[str, Any]] = None
    qc_report: Optional[QCReport] = None
    status: str = "draft"
    refinement_attempts: int = 0
    error_message: Optional[str] = None

class ContentBlockCreate(ContentBlockBase):
    pass

class ContentBlockUpdate(BaseModel):
    block_type: Optional[str] = None
    content_latex: Optional[str] = None
    content_html: Optional[str] = None
    source_llm: Optional[str] = None
    generation_params: Optional[Dict[str, Any]] = None
    qc_report: Optional[QCReport] = None
    status: Optional[str] = None
    refinement_attempts: Optional[int] = None
    error_message: Optional[str] = None

class ContentBlockResponse(ContentBlockBase):
    block_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ExerciseBase(BaseModel):
    version_id: UUID
    prompt_latex: str
    solution_latex: Optional[str] = None
    difficulty: str
    exercise_type: str
    block_id: Optional[UUID] = None # Peut être lié à un content_block spécifique
    source_llm: Optional[str] = None
    qc_report: Optional[QCReport] = None
    status: str = "draft"

class ExerciseCreate(ExerciseBase):
    pass

class ExerciseResponse(ExerciseBase):
    exercise_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WorkflowTaskBase(BaseModel):
    project_id: UUID
    task_type: str
    parameters: Dict[str, Any]
    celery_task_id: Optional[str] = None

class WorkflowTaskCreate(WorkflowTaskBase):
    pass

class WorkflowTaskUpdate(BaseModel):
    status: Optional[str] = None
    celery_task_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    # Permet de mettre à jour des sous-champs dans parameters si nécessaire,
    # mais il est souvent plus simple de passer le dictionnaire complet.
    # parameters: Optional[Dict[str, Any]] = None

class WorkflowTaskResponse(WorkflowTaskBase):
    task_id: UUID
    created_at: datetime
    updated_at: datetime
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class UserFeedbackBase(BaseModel):
    block_id: UUID
    user_id: UUID
    feedback_text: str
    feedback_type: str
    location: Optional[Dict[str, Any]] = None
    status: str = "pending"

class UserFeedbackCreate(UserFeedbackBase):
    pass

class UserFeedbackResponse(UserFeedbackBase):
    feedback_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# --- Modèles pour la Base de Connaissances (KB) ---
# Ces modèles reflètent la structure des données de la KB,
# qu'elle soit stockée en PostgreSQL avancé ou en Neo4j.

class MathematicalConceptBase(BaseModel):
    name: str
    slug: str
    domain: str
    level_min: str
    level_max: Optional[str] = None
    description_short: Optional[str] = None

class MathematicalConceptCreate(MathematicalConceptBase):
    pass

class MathematicalConceptResponse(MathematicalConceptBase):
    concept_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ConceptDefinitionBase(BaseModel):
    concept_id: UUID
    type: str
    level: Optional[str] = None
    content_latex: str
    source: Optional[str] = None
    is_verified: bool = False

class ConceptDefinitionCreate(ConceptDefinitionBase):
    pass

class ConceptDefinitionResponse(ConceptDefinitionBase):
    definition_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class ConceptPropertyBase(BaseModel):
    concept_id: UUID
    name: str
    description_latex: Optional[str] = None
    is_verified: bool = False

class ConceptPropertyCreate(ConceptPropertyBase):
    pass

class ConceptPropertyResponse(ConceptPropertyBase):
    property_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class TheoremBase(BaseModel):
    name: Optional[str] = None
    statement_latex: str
    proof_sketch_latex: Optional[str] = None
    proof_full_latex: Optional[str] = None
    is_verified: bool = False

class TheoremCreate(TheoremBase):
    pass

class TheoremResponse(TheoremBase):
    theorem_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class PedagogicalPitfallBase(BaseModel):
    concept_id: UUID
    description_short: str
    explanation_latex: Optional[str] = None
    level: Optional[str] = None
    is_verified: bool = False

class PedagogicalPitfallCreate(PedagogicalPitfallBase):
    pass

class PedagogicalPitfallResponse(PedagogicalPitfallBase):
    pitfall_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class PedagogicalAnalogyBase(BaseModel):
    concept_id: UUID
    title: Optional[str] = None
    description_latex: str
    domain: Optional[str] = None
    level: Optional[str] = None
    is_verified: bool = False

class PedagogicalAnalogyCreate(PedagogicalAnalogyBase):
    pass

class PedagogicalAnalogyResponse(PedagogicalAnalogyBase):
    analogy_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class ConceptApplicationBase(BaseModel):
    concept_id: UUID
    domain: str
    description_latex: str
    is_verified: bool = False

class ConceptApplicationCreate(ConceptApplicationBase):
    pass

class ConceptApplicationResponse(ConceptApplicationBase):
    application_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class HistoricalNoteBase(BaseModel):
    content_latex: str
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    is_verified: bool = False
    concept_id: Optional[UUID] = None # Peut être lié à un concept
    theorem_id: Optional[UUID] = None # Peut être lié à un théorème

class HistoricalNoteCreate(HistoricalNoteBase):
    pass

class HistoricalNoteResponse(HistoricalNoteBase):
    note_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# Modèles pour les tables de jointure de la KB (si implémenté en PostgreSQL)
class ConceptPrerequisiteBase(BaseModel):
    concept_id: UUID
    prerequisite_concept_id: UUID
    type: str

class ConceptPrerequisiteCreate(ConceptPrerequisiteBase):
    pass

class ConceptPrerequisiteResponse(ConceptPrerequisiteBase):
    # Pas d'ID propre, la PK est composite
    class Config:
        from_attributes = True

class ConceptTheoremRelationBase(BaseModel):
    concept_id: UUID
    theorem_id: UUID
    relation_type: str

class ConceptTheoremRelationCreate(ConceptTheoremRelationBase):
    pass

class ConceptTheoremRelationResponse(ConceptTheoremRelationBase):
    # Pas d'ID propre, la PK est composite
    class Config:
        from_attributes = True
