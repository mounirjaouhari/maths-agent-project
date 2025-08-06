# Fichier placeholder pour feedback_analyzer.py
# backend/interaction-service/refinement/feedback_analyzer.py

import logging
import re
from typing import Dict, Any, Optional, List

from shared.exceptions import BadRequestException, InternalServerError
from shared.models import QCReport # Importe le modèle QCReport si utilisé pour le feedback QC

logger = logging.getLogger(__name__)

class FeedbackAnalyzer:
    """
    Analyse le feedback utilisateur (texte libre ou annotation) ou les rapports QC
    pour en extraire l'intention et les détails structurés.
    """
    def __init__(self):
        logger.info("FeedbackAnalyzer initialisé.")
        # Définir des motifs pour la détection d'intention/type de problème
        self.math_error_patterns = [
            r'\b(erreur|faux|incorrect|pas correct|bug|fausse|problème mathématique)\b',
            r'\b(calcul|preuve|démonstration|formule)\b.*\b(erreur|fausse)\b'
        ]
        self.clarity_patterns = [
            r'\b(pas clair|confus|ambigu|explication|intuitif|comprendre|reformuler)\b',
            r'\b(trop dense|difficile à lire)\b'
        ]
        self.style_patterns = [
            r'\b(style|notation|formulation|ton|jargon)\b'
        ]
        self.suggestion_patterns = [
            r'\b(suggere|propose|ajouter|enlever|modifier|changer)\b'
        ]

    def analyze_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse le feedback pour en extraire l'intention et les détails structurés.
        Le feedback peut provenir de l'utilisateur (texte libre) ou du QC (rapport structuré).
        Args:
            feedback_data (Dict[str, Any]): Dictionnaire du feedback,
                                            ex: { 'source': 'user', 'details': 'Le texte du commentaire', 'location': {...} }
                                            ou { 'source': 'qc', 'qc_report': {...} }
        Returns:
            Dict[str, Any]: Un dictionnaire structuré du feedback analysé.
                            { 'type': 'clarity' | 'math_error' | 'style' | 'suggestion' | 'qc_issue' | 'other',
                              'details': 'Texte nettoyé du feedback ou résumé du problème QC',
                              'location': {...} | None,
                              'confidence': float }
        """
        source = feedback_data.get('source')
        if source == 'user':
            return self._analyze_user_feedback(feedback_data)
        elif source == 'qc':
            return self._analyze_qc_feedback(feedback_data)
        else:
            raise BadRequestException(detail=f"Source de feedback inconnue: {source}")

    def _analyze_user_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse le feedback texte libre de l'utilisateur."""
        feedback_text = feedback_data.get('details', '')
        location = feedback_data.get('location')
        
        cleaned_text = feedback_text.strip().lower()
        
        detected_type = 'other'
        confidence = 0.5 # Confiance par défaut
        
        if any(re.search(pattern, cleaned_text) for pattern in self.math_error_patterns):
            detected_type = 'math_error'
            confidence = 0.9
        elif any(re.search(pattern, cleaned_text) for pattern in self.clarity_patterns):
            detected_type = 'clarity_issue'
            confidence = 0.8
        elif any(re.search(pattern, cleaned_text) for pattern in self.style_patterns):
            detected_type = 'style_mismatch'
            confidence = 0.7
        elif any(re.search(pattern, cleaned_text) for pattern in self.suggestion_patterns):
            detected_type = 'suggestion'
            confidence = 0.7
        
        # Pour des modèles NLP plus sophistiqués, on utiliserait des embeddings, des classifieurs, etc.
        # Exemple: Utilisation d'un modèle de classification de texte (spaCy, Transformers)
        # if self.nlp_model:
        #     doc = self.nlp_model(cleaned_text)
        #     prediction = self.text_classifier(doc)
        #     detected_type = prediction.label
        #     confidence = prediction.score

        return {
            'type': detected_type,
            'details': feedback_text, # Conserver le texte original pour le raffinement
            'location': location,
            'confidence': confidence
        }

    def _analyze_qc_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse le feedback provenant d'un rapport QC."""
        qc_report = QCReport(**feedback_data.get('qc_report', {}))
        critical_errors_only = feedback_data.get('critical_errors_only', False)

        # Extraire le problème le plus sévère ou le plus pertinent du rapport QC
        main_problem: Optional[QCProblem] = None
        for problem in qc_report.problems:
            if critical_errors_only and problem.severity not in ["critical", "major"]:
                continue # Ignorer les problèmes non critiques si demandé

            if not main_problem or self._get_severity_rank(problem.severity) > self._get_severity_rank(main_problem.severity):
                main_problem = problem
            
        if main_problem:
            return {
                'type': main_problem.type,
                'details': main_problem.description,
                'location': main_problem.location,
                'confidence': 1.0 # Le QC est une source de haute confiance
            }
        elif qc_report.status == "failed":
            # Si le QC a échoué mais aucun problème spécifique n'est identifié comme "main_problem"
            return {
                'type': 'qc_issue',
                'details': 'Le rapport QC indique un échec global, mais aucun problème critique n\'a été spécifiquement identifié pour le raffinement.',
                'location': None,
                'confidence': 0.8
            }
        else:
            # Si le QC est passé ou partiel mais qu'il n'y a pas de problème spécifique à raffiner
            return {
                'type': 'no_issue',
                'details': 'Le rapport QC ne signale pas de problème majeur nécessitant un raffinement immédiat.',
                'location': None,
                'confidence': 1.0
            }

    def _get_severity_rank(self, severity: str) -> int:
        """Retourne un rang numérique pour la sévérité d'un problème."""
        ranks = {"critical": 4, "major": 3, "minor": 2, "warning": 1, "other": 0}
        return ranks.get(severity, 0)

# Instancier l'analyseur de feedback
feedback_analyzer = FeedbackAnalyzer()
