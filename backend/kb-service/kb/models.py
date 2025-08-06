# Fichier placeholder pour models.py
# backend/kb-service/kb/models.py

from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

# --- Modèles de Données pour la Base de Connaissances (KB) ---
# Ces modèles sont utilisés pour la représentation des données internes au KB Service
# et pour les schémas d'entrée/sortie de son API interne.

class MathematicalConceptBase(BaseModel):
    """Modèle de base pour un concept mathématique."""
    name: str = Field(..., description="Nom du concept (ex: 'Espace Vectoriel')")
    slug: str = Field(..., description="Identifiant unique et lisible par machine (ex: 'espace_vectoriel')")
    domain: str = Field(..., description="Domaine mathématique principal (ex: 'Algèbre Linéaire')")
    level_min: str = Field(..., description="Niveau pédagogique minimal où le concept est introduit")
    level_max: Optional[str] = Field(None, description="Niveau où le concept est maîtrisé ou approfondi")
    description_short: Optional[str] = Field(None, description="Description concise du concept")

class MathematicalConceptResponse(MathematicalConceptBase):
    """Modèle de réponse pour un concept mathématique, incluant son ID et les horodatages."""
    concept_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ConceptDefinitionBase(BaseModel):
    """Modèle de base pour une définition de concept."""
    concept_id: UUID # L'ID du concept auquel cette définition est liée
    type: str = Field(..., description="Type de définition ('formelle', 'intuitive', 'visuelle')")
    level: Optional[str] = Field(None, description="Niveau spécifique si la définition en dépend")
    content_latex: str = Field(..., description="Le texte de la définition en format LaTeX")
    source: Optional[str] = Field(None, description="Source de la définition (ex: 'standard', 'livre X')")
    is_verified: bool = Field(False, description="Indicateur si cette définition a été vérifiée manuellement ou via un outil formel")

class ConceptDefinitionResponse(ConceptDefinitionBase):
    """Modèle de réponse pour une définition de concept, incluant son ID et l'horodatage."""
    definition_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class ConceptPropertyBase(BaseModel):
    """Modèle de base pour une propriété de concept."""
    concept_id: UUID # L'ID du concept auquel cette propriété est liée
    name: str = Field(..., description="Nom de la propriété (ex: 'Linéarité')")
    description_latex: Optional[str] = Field(None, description="Description ou formulation de la propriété en LaTeX")
    is_verified: bool = Field(False, description="Indicateur si cette propriété a été vérifiée")

class ConceptPropertyResponse(ConceptPropertyBase):
    """Modèle de réponse pour une propriété de concept, incluant son ID et l'horodatage."""
    property_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class TheoremBase(BaseModel):
    """Modèle de base pour un théorème."""
    name: Optional[str] = Field(None, description="Nom du théorème (ex: 'Théorème de la Divergence')")
    statement_latex: str = Field(..., description="Énoncé du théorème en LaTeX")
    proof_sketch_latex: Optional[str] = Field(None, description="Esquisse de preuve en LaTeX")
    proof_full_latex: Optional[str] = Field(None, description="Preuve complète en LaTeX")
    is_verified: bool = Field(False, description="Indicateur si le théorème a été vérifié")

class TheoremResponse(TheoremBase):
    """Modèle de réponse pour un théorème, incluant son ID et l'horodatage."""
    theorem_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class PedagogicalPitfallBase(BaseModel):
    """Modèle de base pour un piège pédagogique."""
    concept_id: UUID # L'ID du concept auquel ce piège est associé
    description_short: str = Field(..., description="Description concise du piège")
    explanation_latex: Optional[str] = Field(None, description="Explication détaillée de pourquoi c'est un piège en LaTeX")
    level: Optional[str] = Field(None, description="Niveau où ce piège est le plus fréquent")
    is_verified: bool = Field(False, description="Indicateur si le piège a été vérifié")

class PedagogicalPitfallResponse(PedagogicalPitfallBase):
    """Modèle de réponse pour un piège pédagogique, incluant son ID et l'horodatage."""
    pitfall_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class PedagogicalAnalogyBase(BaseModel):
    """Modèle de base pour une analogie pédagogique."""
    concept_id: UUID # L'ID du concept illustré par l'analogie
    title: Optional[str] = Field(None, description="Titre court de l'analogie")
    description_latex: str = Field(..., description="Description détaillée de l'analogie en LaTeX")
    domain: Optional[str] = Field(None, description="Domaine de l'analogie (ex: 'Physique', 'Finance')")
    level: Optional[str] = Field(None, description="Niveau où cette analogie est la plus pertinente")
    is_verified: bool = Field(False, description="Indicateur si l'analogie a été vérifiée")

class PedagogicalAnalogyResponse(PedagogicalAnalogyBase):
    """Modèle de réponse pour une analogie pédagogique, incluant son ID et l'horodatage."""
    analogy_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class ConceptApplicationBase(BaseModel):
    """Modèle de base pour une application de concept."""
    concept_id: UUID # L'ID du concept appliqué
    domain: str = Field(..., description="Domaine d'application (ex: 'Ingénierie', 'Économie')")
    description_latex: str = Field(..., description="Description de l'application en LaTeX")
    is_verified: bool = Field(False, description="Indicateur si l'application a été vérifiée")

class ConceptApplicationResponse(ConceptApplicationBase):
    """Modèle de réponse pour une application de concept, incluant son ID et l'horodatage."""
    application_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class HistoricalNoteBase(BaseModel):
    """Modèle de base pour une note historique."""
    content_latex: str = Field(..., description="Le texte de la note historique en LaTeX")
    date_start: Optional[datetime] = Field(None, description="Date de début de la période concernée")
    date_end: Optional[datetime] = Field(None, description="Date de fin de la période concernée")
    is_verified: bool = Field(False, description="Indicateur si la note a été vérifiée")
    concept_id: Optional[UUID] = Field(None, description="ID du concept associé (si applicable)")
    theorem_id: Optional[UUID] = Field(None, description="ID du théorème associé (si applicable)")

class HistoricalNoteResponse(HistoricalNoteBase):
    """Modèle de réponse pour une note historique, incluant son ID et l'horodatage."""
    note_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# --- Modèles pour les relations de la KB (si implémenté en PostgreSQL) ---
# Ces modèles représentent les tables de jointure pour les relations Many-to-Many.

class ConceptPrerequisiteBase(BaseModel):
    """Modèle de base pour une relation de prérequis entre concepts."""
    concept_id: UUID # Le concept qui requiert un autre concept
    prerequisite_concept_id: UUID # Le concept qui est un prérequis
    type: str = Field("required", description="Type de prérequis ('required', 'recommended')")

class ConceptPrerequisiteResponse(ConceptPrerequisiteBase):
    """Modèle de réponse pour une relation de prérequis."""
    # Pas d'ID propre, la PK est composite
    class Config:
        from_attributes = True

class ConceptTheoremRelationBase(BaseModel):
    """Modèle de base pour une relation entre un concept et un théorème."""
    concept_id: UUID
    theorem_id: UUID
    relation_type: str = Field(..., description="Type de relation ('defines', 'uses', 'is_example_of')")

class ConceptTheoremRelationResponse(ConceptTheoremRelationBase):
    """Modèle de réponse pour une relation concept-théorème."""
    # Pas d'ID propre, la PK est composite
    class Config:
        from_attributes = True
