# Fichier placeholder pour schemas.py
# backend/api-gateway/api/v1/schemas.py

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

# --- Schémas pour les utilisateurs ---

class UserRegister(BaseModel):
    """Schéma pour l'enregistrement d'un nouvel utilisateur."""
    username: str = Field(..., example="user@example.com", description="Nom d'utilisateur (généralement un email)")
    password: str = Field(..., min_length=8, example="securepassword123", description="Mot de passe de l'utilisateur")
    is_active: bool = True
    role: str = "user"

class UserLogin(BaseModel):
    """Schéma pour la connexion d'un utilisateur."""
    username: str = Field(..., example="user@example.com", description="Nom d'utilisateur")
    password: str = Field(..., example="securepassword123", description="Mot de passe")

class LoginResponse(BaseModel):
    """Schéma de réponse après une connexion réussie."""
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = "bearer"

class UserResponse(BaseModel):
    """Schéma de réponse pour les informations utilisateur."""
    user_id: UUID
    username: str
    created_at: datetime
    is_active: bool
    role: str

    class Config:
        from_attributes = True # Permet de mapper depuis des objets ORM (SQLAlchemy)

# --- Schémas pour les projets ---

class ProjectCreate(BaseModel):
    """Schéma pour la création d'un nouveau projet."""
    title: str = Field(..., example="Introduction à l'Algèbre Linéaire", description="Titre du projet/document")
    subject: str = Field(..., example="Algèbre Linéaire", description="Sujet mathématique principal")
    level: str = Field(..., example="L2", description="Niveau pédagogique cible (ex: L1, L2, M1, Lycée)")
    style: str = Field(..., example="Hybride", description="Style rédactionnel choisi (Bourbaki, Feynman, Hybride)")
    mode: str = Field(..., example="Supervisé", description="Mode de fonctionnement choisi (Supervisé, Autonome)")

class ProjectUpdate(BaseModel):
    """Schéma pour la mise à jour d'un projet existant."""
    title: Optional[str] = None
    subject: Optional[str] = None
    level: Optional[str] = None
    style: Optional[str] = None
    mode: Optional[str] = None
    status: Optional[str] = None # Statut du projet (draft, in_progress, completed, archived)
    current_step: Optional[str] = None # Étape actuelle du workflow (pour mode Supervisé)

class ProjectResponse(BaseModel):
    """Schéma de réponse pour les informations de base d'un projet."""
    project_id: UUID
    user_id: UUID
    title: str
    subject: str
    level: str
    style: str
    mode: str
    created_at: datetime
    updated_at: datetime
    status: str
    current_step: Optional[str] = None

    class Config:
        from_attributes = True

class QCProblem(BaseModel):
    """Schéma pour un problème détecté par le module QC."""
    type: str = Field(..., example="math_error", description="Type de problème (ex: math_error, clarity_issue)")
    severity: str = Field(..., example="critical", description="Sévérité du problème (critical, major, minor, warning)")
    description: str = Field(..., example="L'égalité $x^2+y^2=0$ n'est vraie que si $x=0$ et $y=0$, pas pour tout $x,y$.", description="Description détaillée du problème")
    location: Optional[Dict[str, Any]] = Field(None, example={'line': 10, 'char_start': 5, 'char_end': 15}, description="Localisation précise du problème dans le contenu")
    suggested_fix: Optional[str] = Field(None, description="Suggestion de correction (si l'IA peut la formuler)")

class QCReport(BaseModel):
    """Schéma pour le rapport de contrôle qualité d'un bloc de contenu."""
    overall_score: float = Field(..., ge=0, le=100, example=85.5, description="Score global de qualité (0-100)")
    status: str = Field(..., example="failed", description="Statut du rapport (passed, failed, partial_success)")
    problems: List[QCProblem] = Field([], description="Liste des problèmes détectés")
    details: Optional[Dict[str, Any]] = Field(None, description="Détails bruts des analyses par sous-module (math, pedago, coherence)")

class ContentBlockResponse(BaseModel):
    """Schéma de réponse pour un bloc de contenu."""
    block_id: UUID
    version_id: UUID
    block_type: str
    content_latex: str
    content_html: Optional[str] = None
    source_llm: Optional[str] = None
    generation_params: Optional[Dict[str, Any]] = None
    qc_report: Optional[QCReport] = None
    status: str
    created_at: datetime
    updated_at: datetime
    refinement_attempts: int
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class ProjectDetailResponse(ProjectResponse):
    """Schéma de réponse détaillé pour un projet, incluant la structure du document et les blocs de contenu."""
    document_structure: Dict[str, Any] = Field(..., description="Structure hiérarchique du document (chapitres, sections, blocs)")
    content_blocks: List[ContentBlockResponse] = Field([], description="Liste des blocs de contenu détaillés du document")

    class Config:
        from_attributes = True

class WorkflowSignal(BaseModel):
    """Schéma pour un signal envoyé au moteur de workflow par l'utilisateur."""
    signal_type: str = Field(..., description="Type de signal (ex: VALIDATED, REDO, ADD_ELEMENT)",
                             examples=["VALIDATED", "REDO", "ADD_ELEMENT", "QC_OK", "PROBLEM_DETECTED", "ALL_APPROVED", "CANCEL_PROJECT"])
    block_id: Optional[UUID] = Field(None, description="ID du bloc de contenu concerné par le signal (si applicable)")
    feedback: Optional[Dict[str, Any]] = Field(None, description="Détails du feedback utilisateur pour les signaux REDO")

