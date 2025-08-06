# Fichier placeholder pour pedagogic_analyzer.py
# backend/qc-service/qc/pedagogic_analyzer.py

import logging
import httpx
import re
from typing import Dict, Any, List, Optional
from uuid import UUID

from shared.config import get_settings
from shared.exceptions import InternalServerError, BadRequestException
from shared.models import QCProblem # Importe le modèle pour les problèmes QC

logger = logging.getLogger(__name__)
settings = get_settings()

class PedagogicAnalyzer:
    """
    Sous-module d'Analyse Pédagogique et Stylistique du QC Service.
    Évalue la clarté, l'accessibilité, la pertinence pédagogique et la cohérence stylistique
    du contenu généré.
    """
    def __init__(self, kb_service_url: str):
        self.kb_service_url = kb_service_url

    async def _get_kb_data_for_concept(self, concept_id: UUID, level: str) -> Dict[str, Any]:
        """
        Récupère les pièges, analogies et applications pertinentes pour un concept
        depuis le KB Service.
        """
        async with httpx.AsyncClient() as client:
            try:
                pitfalls_resp = await client.get(f"{self.kb_service_url}/internal/concepts/{concept_id}/pitfalls", params={"level": level})
                pitfalls_resp.raise_for_status()
                pitfalls = pitfalls_resp.json()

                analogies_resp = await client.get(f"{self.kb_service_url}/internal/concepts/{concept_id}/analogies", params={"level": level})
                analogies_resp.raise_for_status()
                analogies = analogies_resp.json()

                applications_resp = await client.get(f"{self.kb_service_url}/internal/concepts/{concept_id}/applications")
                applications_resp.raise_for_status()
                applications = applications_resp.json()

                return {
                    "pitfalls": pitfalls,
                    "analogies": analogies,
                    "applications": applications
                }
            except httpx.HTTPStatusError as e:
                logger.warning(f"KB Service returned HTTP error for concept {concept_id}: {e.response.text}")
                return {"pitfalls": [], "analogies": [], "applications": []}
            except httpx.RequestError as e:
                logger.error(f"Network error calling KB Service for concept {concept_id}: {e}")
                raise InternalServerError(detail="Impossible de se connecter au KB Service.")

    def _calculate_flesch_kincaid(self, text: str) -> float:
        """
        Calcule l'indice de lisibilité Flesch-Kincaid.
        Adapte le texte en ignorant le contenu LaTeX pour un calcul plus pertinent.
        """
        # Supprimer le contenu LaTeX des formules inline et des blocs pour le calcul de lisibilité
        cleaned_text = re.sub(r'\$.*?\$', '', text) # Supprime $...$
        cleaned_text = re.sub(r'\\\[.*?\\\]', '', cleaned_text, flags=re.DOTALL) # Supprime \[...\]
        cleaned_text = re.sub(r'\\begin\{.*?\}\s*.*?\\end\{.*?\}', '', cleaned_text, flags=re.DOTALL) # Supprime \begin{...}\end{...}

        words = re.findall(r'\b\w+\b', cleaned_text.lower())
        sentences = re.split(r'[.!?]+\s*', cleaned_text)
        sentences = [s for s in sentences if s.strip()] # Supprime les phrases vides

        num_words = len(words)
        num_sentences = len(sentences)
        num_syllables = sum(self._count_syllables(word) for word in words)

        if num_words == 0 or num_sentences == 0:
            return 0.0 # Éviter la division par zéro

        # Formule Flesch-Kincaid Grade Level
        score = 0.39 * (num_words / num_sentences) + 11.8 * (num_syllables / num_words) - 15.59
        return score

    def _count_syllables(self, word: str) -> int:
        """Compte le nombre de syllabes dans un mot (très simplifié)."""
        # Ceci est une heuristique très basique et ne sera pas précise pour tous les mots,
        # en particulier les termes techniques. Une bibliothèque NLP plus avancée serait préférable.
        vowels = "aeiouy"
        count = 0
        if not word:
            return 0
        word = word.lower()
        if word[0] in vowels:
            count += 1
        for index in range(1, len(word)):
            if word[index] in vowels and word[index - 1] not in vowels:
                count += 1
        if word.endswith("e"):
            count -= 1
        if word.endswith("le") and len(word) > 2 and word[-3] not in vowels:
            count += 1 # handle "able"
        if count == 0:
            count = 1 # Chaque mot a au moins une syllabe
        return count

    async def analyze_pedagogic_and_style(self, content_latex: str, block_type: str, level: str, style: str, concept_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Analyse la pertinence pédagogique et la cohérence stylistique du contenu.
        Args:
            content_latex (str): Le contenu du bloc en LaTeX.
            block_type (str): Type du bloc (ex: 'definition', 'intuition').
            level (str): Niveau pédagogique cible.
            style (str): Style rédactionnel (ex: 'Bourbaki', 'Feynman').
            concept_id (Optional[UUID]): ID du concept principal si pertinent.
        Returns:
            Dict[str, Any]: Un rapport d'analyse pédagogique/stylistique.
        """
        problems: List[QCProblem] = []
        pedagogic_score = 100.0 # Commence avec un score parfait
        
        # 1. Analyse de Lisibilité
        flesch_kincaid_score = self._calculate_flesch_kincaid(content_latex)
        logger.info(f"Flesch-Kincaid score: {flesch_kincaid_score} for block type {block_type}")
        
        # Exemple de règles de lisibilité (à affiner)
        if level == "Lycée" and flesch_kincaid_score > 12:
            problems.append(QCProblem(type="clarity_issue", severity="minor", description=f"Le texte est trop complexe pour le niveau Lycée (Flesch-Kincaid: {flesch_kincaid_score:.2f})."))
            pedagogic_score -= 5
        elif level in ["L1", "L2"] and flesch_kincaid_score > 15:
            problems.append(QCProblem(type="clarity_issue", severity="minor", description=f"Le texte est potentiellement trop complexe pour le niveau {level} (Flesch-Kincaid: {flesch_kincaid_score:.2f})."))
            pedagogic_score -= 3
        
        # 2. Détection des Pièges Pédagogiques et Pertinence des Analogies (si concept_id fourni)
        if concept_id:
            kb_data = await self._get_kb_data_for_concept(concept_id, level)
            
            # Vérifier si le contenu aborde les pièges connus
            for pitfall in kb_data["pitfalls"]:
                if pitfall.get("is_verified") and pitfall.get("description_short").lower() in content_latex.lower():
                    # Si le piège est mentionné, c'est bien. Sinon, c'est une omission potentielle.
                    pass # Logique plus complexe pour vérifier si le piège est "abordé" ou "évité"
                else:
                    problems.append(QCProblem(type="pedagogic_pitfall", severity="warning", description=f"Piège pédagogique potentiel non abordé: '{pitfall.get('description_short')}'."))
                    pedagogic_score -= 10
            
            # Vérifier la présence et la qualité des analogies pour le style Feynman
            if style == "Feynman" and block_type == "intuition":
                if not any(analogy.get("description_latex").lower() in content_latex.lower() for analogy in kb_data["analogies"]):
                    problems.append(QCProblem(type="clarity_issue", severity="major", description="Manque d'analogie pertinente pour un style Feynman intuitif."))
                    pedagogic_score -= 15
                # Logique plus complexe pour évaluer la qualité de l'analogie si présente

        # 3. Analyse de Cohérence Stylistique
        # Très simplifié: Vérifier la présence de certains mots-clés ou structures de phrases
        if style == "Bourbaki":
            if re.search(r'\b(intuitive|imaginez|pensez|simplement)\b', content_latex, re.IGNORECASE):
                problems.append(QCProblem(type="style_mismatch", severity="minor", description="Le style Bourbaki ne devrait pas contenir de langage intuitif."))
                pedagogic_score -= 5
            if not re.search(r'\b(Soit|Pour tout|Il existe)\b', content_latex):
                problems.append(QCProblem(type="style_mismatch", severity="minor", description="Le style Bourbaki manque de formalisme attendu."))
                pedagogic_score -= 5
        elif style == "Feynman":
            if re.search(r'\b(démonstration formelle|axiome|lemme)\b', content_latex, re.IGNORECASE):
                problems.append(QCProblem(type="style_mismatch", severity="minor", description="Le style Feynman ne devrait pas être trop formel."))
                pedagogic_score -= 5
        
        # Assurer que le score ne descend pas en dessous de zéro
        pedagogic_score = max(0.0, pedagogic_score)

        return {
            "score": pedagogic_score,
            "problems": [p.model_dump() for p in problems],
            "details": {
                "flesch_kincaid_score": flesch_kincaid_score,
                "level_target": level,
                "style_target": style
            }
        }

