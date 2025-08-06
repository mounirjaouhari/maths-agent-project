# Fichier placeholder pour utils.py
# backend/shared/utils.py

import uuid
from datetime import datetime, timezone

def generate_uuid() -> str:
    """
    Génère un identifiant unique universel (UUID) sous forme de chaîne de caractères.
    Utilisé pour les IDs des entités comme les utilisateurs, projets, blocs de contenu, etc.
    """
    return str(uuid.uuid4())

def get_current_utc_timestamp() -> datetime:
    """
    Retourne l'horodatage UTC actuel avec les informations de fuseau horaire.
    Utile pour les champs created_at et updated_at dans les modèles de base de données.
    """
    return datetime.now(timezone.utc)

def sanitize_latex_input(latex_string: str) -> str:
    """
    Nettoie une chaîne LaTeX pour supprimer les caractères potentiellement dangereux
    ou les constructions non désirées avant le rendu ou la compilation.
    Ceci est une étape de sécurité et de pré-traitement.
    NOTE: Une désinfection complète et robuste du LaTeX est complexe et pourrait
    nécessiter des bibliothèques dédiées ou des outils externes plus avancés.
    Cette fonction est un exemple basique.
    """
    # Exemple: Supprimer les commandes d'inclusion de fichiers
    sanitized_string = latex_string.replace("\\input", "")
    sanitized_string = sanitized_string.replace("\\include", "")
    # Supprimer les commandes d'exécution de shell (si elles étaient supportées)
    sanitized_string = sanitized_string.replace("\\write18", "")
    
    # Vous pouvez ajouter plus de règles de désinfection ici
    # Ex: Échapper certains caractères spéciaux si nécessaire pour éviter l'injection XSS dans un contexte HTML
    # (bien que le rendu LaTeX devrait gérer cela, c'est une couche de défense supplémentaire)

    return sanitized_string

