# Fichier placeholder pour score_calculator.py
# backend/qc-service/qc/score_calculator.py

import logging
from typing import Dict, Any, List, Optional

from shared.models import QCReport, QCProblem # Importe les modèles pour les rapports QC

logger = logging.getLogger(__name__)

class ScoreCalculator:
    """
    Calcule le score de confiance global pour un bloc de contenu
    en synthétisant les résultats des différents sous-modules QC.
    """
    def __init__(self):
        # Poids pour chaque type d'analyse (ajuster selon l'importance)
        self.weights = {
            "math": 0.5,        # Poids de la vérification mathématique
            "pedagogic": 0.3,   # Poids de l'analyse pédagogique et stylistique
            "coherence": 0.2    # Poids de l'analyse de cohérence
        }
        # Seuils pour la détermination du statut global du rapport QC
        self.overall_score_thresholds = {
            "passed": 90,       # Score >= 90 pour un succès complet
            "partial_success": 60 # Score >= 60 pour un succès partiel (avec des problèmes mineurs)
        }
        # Pénalités pour les sévérités de problèmes
        self.severity_penalties = {
            "critical": 50,     # Une erreur critique réduit massivement le score
            "major": 20,        # Une erreur majeure réduit significativement
            "minor": 5,         # Une erreur mineure réduit légèrement
            "warning": 0        # Un avertissement n'affecte pas le score directement, mais est signalé
        }

    def calculate_overall_score(self, 
                                math_report: Dict[str, Any], 
                                pedagogic_report: Dict[str, Any], 
                                coherence_report: Dict[str, Any]) -> QCReport:
        """
        Calcule le score de confiance global et génère le rapport QC final.
        Args:
            math_report (Dict[str, Any]): Rapport du MathVerifier.
            pedagogic_report (Dict[str, Any]): Rapport du PedagogicAnalyzer.
            coherence_report (Dict[str, Any]): Rapport du CoherenceAnalyzer.
        Returns:
            QCReport: Le rapport QC final structuré.
        """
        problems: List[QCProblem] = []
        overall_score = 0.0
        
        # Collecter les problèmes de tous les rapports
        problems.extend([QCProblem(**p) for p in math_report.get("problems", [])])
        problems.extend([QCProblem(**p) for p in pedagogic_report.get("problems", [])])
        problems.extend([QCProblem(**p) for p in coherence_report.get("problems", [])])

        # Calculer le score pondéré des sous-modules
        math_score = math_report.get("confidence", 0.0) * 100 # Convertir confiance (0-1) en score (0-100)
        pedagogic_score = pedagogic_report.get("score", 0.0)
        coherence_score = coherence_report.get("score", 0.0)

        overall_score = (
            self.weights["math"] * math_score +
            self.weights["pedagogic"] * pedagogic_score +
            self.weights["coherence"] * coherence_score
        )
        
        # Appliquer les pénalités pour les problèmes détectés
        for problem in problems:
            penalty = self.severity_penalties.get(problem.severity, 0)
            overall_score -= penalty
            if problem.severity == "critical":
                # Si une erreur critique est présente, le score ne peut pas dépasser un certain seuil bas
                overall_score = min(overall_score, 20.0) # Ex: max 20 si erreur critique

        # S'assurer que le score reste dans la plage 0-100
        overall_score = max(0.0, min(100.0, overall_score))

        # Déterminer le statut global du rapport
        report_status = "failed"
        if overall_score >= self.overall_score_thresholds["passed"]:
            report_status = "passed"
        elif overall_score >= self.overall_score_thresholds["partial_success"]:
            report_status = "partial_success"
        
        # Si des problèmes critiques sont présents, le statut est toujours 'failed'
        if any(p.severity == "critical" for p in problems):
            report_status = "failed"

        logger.info(f"Calcul du score global: Math={math_score:.2f}, Pédago={pedagogic_score:.2f}, Cohérence={coherence_score:.2f} -> Global={overall_score:.2f}, Statut={report_status}")

        return QCReport(
            overall_score=overall_score,
            status=report_status,
            problems=problems,
            details={
                "math_report_details": math_report,
                "pedagogic_report_details": pedagogic_report,
                "coherence_report_details": coherence_report
            }
        )

# Instancier le calculateur de score
score_calculator = ScoreCalculator()
