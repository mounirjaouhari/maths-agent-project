# backend/api-gateway/api/v1/endpoints/users.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import httpx
import logging

from shared.config import get_settings
from shared.models import UserRegister, UserResponse, UserBase
from shared.exceptions import BadRequestException, ConflictException, UnauthorizedException, ServiceUnavailableException
from ..auth import security

router = APIRouter()
logger = logging.getLogger(__name__)

settings = get_settings()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Enregistrer un nouvel utilisateur")
async def register_user(user_data: UserRegister):
    """
    Enregistre un nouvel utilisateur dans le système.
    Le mot de passe est haché avant d'être envoyé au service de persistance.
    """
    try:
        # Hacher le mot de passe avant de l'envoyer au service de persistance
        hashed_password = security.get_password_hash(user_data.password)
        
        # Préparer les données pour le service de persistance
        user_create_data = {
            "username": user_data.username,
            "password_hash": hashed_password,
            "is_active": user_data.is_active,
            "role": user_data.role
        }

        # Appeler le service de persistance pour créer l'utilisateur
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.PERSISTENCE_SERVICE_URL}/internal/users",
                json=user_create_data
            )
            response.raise_for_status() # Lève une exception pour les codes d'erreur HTTP (4xx, 5xx)
            
            # Le service de persistance retourne les données de l'utilisateur créé
            created_user = response.json()
            return UserResponse(**created_user)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == status.HTTP_409_CONFLICT:
            raise ConflictException(detail=f"Le nom d'utilisateur '{user_data.username}' existe déjà.")
        logger.error(f"Erreur lors de l'appel au service de persistance pour l'enregistrement: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail="Erreur du service de persistance lors de l'enregistrement.")
    except httpx.RequestError as e:
        logger.error(f"Erreur réseau lors de l'appel au service de persistance: {e}")
        raise ServiceUnavailableException(detail="Le service de persistance n'est pas disponible.")
    except Exception as e:
        logger.error(f"Erreur inattendue lors de l'enregistrement de l'utilisateur: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur.")


@router.post("/login", summary="Connecter un utilisateur et obtenir un jeton JWT")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authentifie un utilisateur et retourne un jeton d'accès JWT.
    """
    try:
        # Appeler le service de persistance pour récupérer l'utilisateur par nom d'utilisateur
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.PERSISTENCE_SERVICE_URL}/internal/users/username/{form_data.username}"
            )
            response.raise_for_status()
            user_data = response.json()
            user = UserBase(**user_data) # Utiliser UserBase car le mot de passe haché n'est pas exposé ici
            user.password_hash = user_data.get("password_hash") # Récupérer le hash du mot de passe pour la vérification

        if not user:
            raise UnauthorizedException(detail="Nom d'utilisateur ou mot de passe incorrect.")
        
        # Vérifier le mot de passe haché
        if not security.verify_password(form_data.password, user.password_hash):
            raise UnauthorizedException(detail="Nom d'utilisateur ou mot de passe incorrect.")
        
        # Créer le jeton d'accès JWT
        access_token_expires = security.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            data={"sub": user.username, "user_id": str(user.user_id), "role": user.role}, 
            expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == status.HTTP_404_NOT_FOUND:
            raise UnauthorizedException(detail="Nom d'utilisateur ou mot de passe incorrect.")
        logger.error(f"Erreur lors de l'appel au service de persistance pour la connexion: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail="Erreur du service de persistance lors de la connexion.")
    except httpx.RequestError as e:
        logger.error(f"Erreur réseau lors de l'appel au service de persistance: {e}")
        raise ServiceUnavailableException(detail="Le service de persistance n'est pas disponible.")
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la connexion de l'utilisateur: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur.")

