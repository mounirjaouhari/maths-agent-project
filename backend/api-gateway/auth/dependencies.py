# Fichier placeholder pour dependencies.py
# backend/api-gateway/auth/dependencies.py

import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from shared.exceptions import ForbiddenException, UnauthorizedException

from .security import (  # Importe le schéma OAuth2 et la fonction de décodage
    decode_access_token, oauth2_scheme,
)

logger = logging.getLogger(__name__)


# Dépendance pour obtenir l'ID de l'utilisateur authentifié
async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """
    Dépendance FastAPI pour récupérer l'ID de l'utilisateur à partir du jeton JWT.
    Lève une UnauthorizedException si le jeton est invalide ou expiré.
    """
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise UnauthorizedException(
                detail="Jeton invalide: ID utilisateur manquant.")
        return user_id
    except Exception as e:
        logger.error(
            f"Erreur inattendue lors de la récupération de l'ID utilisateur à partir du jeton: {e}",
            exc_info=True,
        )
        raise UnauthorizedException(detail="Jeton invalide ou erreur interne.")


# Dépendance pour obtenir l'utilisateur authentifié (avec son rôle)
async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Dépendance FastAPI pour récupérer le payload complet de l'utilisateur à partir du jeton JWT.
    Lève une UnauthorizedException si le jeton est invalide ou expiré.
    """
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        user_role: str = payload.get("role")

        if username is None or user_id is None or user_role is None:
            raise UnauthorizedException(
                detail="Jeton invalide: informations utilisateur incomplètes.")

        return {"username": username, "user_id": user_id, "role": user_role}
    except Exception as e:
        logger.error(
            f"Erreur inattendue lors de la récupération de l'utilisateur à partir du jeton: {e}",
            exc_info=True,
        )
        raise UnauthorizedException(detail="Jeton invalide ou erreur interne.")


# Dépendance pour vérifier si l'utilisateur est un administrateur
async def require_admin_role(current_user: dict = Depends(get_current_user)):
    """
    Dépendance FastAPI pour s'assurer que l'utilisateur authentifié a le rôle 'admin'.
    Lève une ForbiddenException si l'utilisateur n'est pas un administrateur.
    """
    if current_user.get("role") != "admin":
        raise ForbiddenException(
            detail="Accès requis pour les administrateurs.")
    return current_user


# Vous pouvez ajouter d'autres dépendances d'autorisation ici, par exemple:
# async def require_specific_permission(current_user: dict = Depends(get_current_user)):
#     if "permission_name" not in current_user.get("permissions", []):
#         raise ForbiddenException(detail="Permission insuffisante.")
#     return current_user
