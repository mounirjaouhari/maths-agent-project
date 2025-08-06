# Fichier placeholder pour coherence_analyzer.py
# backend/qc-service/qc/coherence_analyzer.py

import logging
import httpx
import re
from typing import Dict, Any, List, Optional
from uuid import UUID

from shared.config import get_settings
from shared.exceptions import InternalServerError, BadRequestException, NotFoundException
from shared.models import QCProblem, ContentBlockResponse # Importe les modèles pour les problèmes QC et les blocs de contenu

logger = logging.getLogger(__name__)
settings = get_settings()

class CoherenceAnalyzer:
    """
    Sous-module de Cohérence Globale du QC Service.
    Se concentre sur l'analyse des relations et des consistances à travers
    différentes parties du document généré.
    """
    def __init__(self, kb_service_url: str, persistence_service_url: str):
        self.kb_service_url = kb_service_url
        self.persistence_service_url = persistence_service_url

    async def _get_kb_concept_data(self, concept_id: UUID) -> Dict[str, Any]:
        """Récupère les données d'un concept depuis le KB Service."""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{self.kb_service_url}/internal/concepts/{concept_id}")
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.warning(f"Concept {concept_id} non trouvé dans la KB.")
                    return None
                logger.error(f"Erreur HTTP lors de l'appel au KB Service pour concept {concept_id}: {e.response.text}")
                raise InternalServerError(detail="Erreur lors de l'accès au KB Service.")
            except httpx.RequestError as e:
                logger.error(f"Erreur réseau lors de l'appel au KB Service pour concept {concept_id}: {e}")
                raise InternalServerError(detail="Impossible de se connecter au KB Service.")

    async def _get_all_blocks_for_version(self, document_version_id: UUID) -> List[ContentBlockResponse]:
        """Récupère tous les blocs de contenu validés pour une version de document."""
        async with httpx.AsyncClient() as client:
            try:
                # Cet endpoint doit être implémenté dans le service de persistance pour lister par version
                resp = await client.get(f"{self.persistence_service_url}/internal/content-blocks", params={"version_id": str(document_version_id), "status": "validated"})
                resp.raise_for_status()
                return [ContentBlockResponse(**b) for b in resp.json()]
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise NotFoundException(detail=f"Version de document {document_version_id} non trouvée.")
                logger.error(f"Erreur HTTP lors de la récupération des blocs pour la version {document_version_id}: {e.response.text}")
                raise InternalServerError(detail="Erreur lors de l'accès au Persistence Service.")
            except httpx.RequestError as e:
                logger.error(f"Erreur réseau lors de la récupération des blocs pour la version {document_version_id}: {e}")
                raise InternalServerError(detail="Impossible de se connecter au Persistence Service.")

    async def analyze_coherence(self, document_version_id: UUID, scope: str = 'document') -> Dict[str, Any]:
        """
        Déclenche une analyse de cohérence sur une partie ou l'intégralité d'une version de document.
        Args:
            document_version_id (UUID): L'ID de la version du document à analyser.
            scope (str): Portée de l'analyse ('section', 'chapter', 'document').
        Returns:
            Dict[str, Any]: Un rapport de cohérence.
        """
        problems: List[QCProblem] = []
        coherence_score = 100.0 # Commence avec un score parfait

        # Récupérer tous les blocs de contenu validés pour la version du document
        all_blocks = await self._get_all_blocks_for_version(document_version_id)
        if not all_blocks:
            return {
                "score": 100.0,
                "problems": [],
                "details": {"message": "Aucun bloc validé à analyser pour la cohérence."}
            }

        # Concaténer tout le contenu LaTeX pour l'analyse globale
        full_latex_content = "\n\n".join([block.content_latex for block in all_blocks])

        # 1. Vérification de la Cohérence de la Notation
        notation_issues = self._check_notation_consistency(full_latex_content)
        if notation_issues:
            problems.extend(notation_issues)
            coherence_score -= len(notation_issues) * 5 # Pénalité pour chaque problème
            logger.warning(f"Problèmes de notation détectés: {notation_issues}")

        # 2. Détection des Répétitions et Redondances
        redundancy_issues = self._check_for_redundancies(full_latex_content)
        if redundancy_issues:
            problems.extend(redundancy_issues)
            coherence_score -= len(redundancy_issues) * 3
            logger.warning(f"Redondances détectées: {redundancy_issues}")

        # 3. Vérification des Références Croisées et des Prérequis (nécessite la structure du document)
        # Pour cette analyse, nous aurions besoin de la structure du document (content_structure)
        # et de la capacité d'extraire les concepts utilisés dans chaque bloc.
        # Cette partie est conceptuelle et dépendrait d'un parseur LaTeX plus avancé
        # et d'une logique de parcours de l'arborescence du document.
        
        # Exemple: Simuler la détection d'un concept utilisé avant sa définition
        # Pour cela, il faudrait:
        # a) Extraire les concepts mentionnés dans chaque bloc.
        # b) Connaître l'ordre des blocs dans la structure du document.
        # c) Interroger le KB Service pour les prérequis et définitions.
        
        # Pour l'exemple, nous allons simuler un problème si un mot clé est trouvé avant un autre
        if "dérivée" in full_latex_content.lower() and "limite" not in full_latex_content.lower():
            problems.append(QCProblem(type="coherence_issue", severity="major", description="Le concept de 'dérivée' est utilisé sans que 'limite' ne soit mentionné, ce qui peut indiquer un prérequis manquant."))
            coherence_score -= 20
        
        # Assurer que le score ne descend pas en dessous de zéro
        coherence_score = max(0.0, coherence_score)

        return {
            "score": coherence_score,
            "problems": [p.model_dump() for p in problems],
            "details": {
                "scope_analyzed": scope,
                "num_blocks_analyzed": len(all_blocks)
            }
        }

    def _check_notation_consistency(self, text: str) -> List[QCProblem]:
        """
        Vérifie la cohérence de la notation mathématique.
        Très simplifié: cherche des variations pour le même concept.
        """
        issues: List[QCProblem] = []
        # Exemple: Utilisation de 'vec{v}' et 'mathbf{v}' pour le même vecteur
        if re.search(r'\\vec\{v\}', text) and re.search(r'\\mathbf\{v\}', text):
            issues.append(QCProblem(type="coherence_issue", severity="minor", description="Notation inconsistante pour les vecteurs (\\vec{v} et \\mathbf{v} utilisés)."))
        # Exemple: Utilisation de 'dx' et 'partial x' pour la même différentielle
        if re.search(r'dx', text) and re.search(r'\\partial x', text):
            issues.append(QCProblem(type="coherence_issue", severity="minor", description="Notation inconsistante pour la différentielle (dx et \\partial x utilisés)."))
        return issues

    def _check_for_redundancies(self, text: str) -> List[QCProblem]:
        """
        Détecte les répétitions excessives de phrases ou d'explications.
        Très simplifié: cherche les phrases qui se répètent exactement.
        Une analyse NLP plus avancée (embeddings, similarité sémantique) serait nécessaire.
        """
        issues: List[QCProblem] = []
        sentences = re.split(r'(?<=[.!?])\s+', text) # Divise le texte en phrases
        sentence_counts = {}
        for sentence in sentences:
            clean_sentence = sentence.strip().lower()
            if len(clean_sentence) > 20: # Ignorer les phrases très courtes
                sentence_counts[clean_sentence] = sentence_counts.get(clean_sentence, 0) + 1
        
        for sentence, count in sentence_counts.items():
            if count > 1: # Si une phrase se répète
                issues.append(QCProblem(type="coherence_issue", severity="minor", description=f"Phrase répétée excessivement: '{sentence[:50]}...' ({count} fois)."))
        return issues

