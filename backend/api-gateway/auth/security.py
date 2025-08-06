# backend/api-gateway/auth/security.py

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
import logging

from shared.config import get_settings
from shared.exceptions import UnauthorizedException

logger = logging.getLogger(__name__)

# Charge les paramètres de configuration
settings = get_settings()

# Contexte pour le hachage des mots de passe (utilisation de bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Schéma OAuth2 pour la récupération du jeton Bearer (JWT) depuis l'en-tête Authorization
# L'URL /v1/users/login est l'endpoint où le client peut obtenir un jeton
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/users/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie si un mot de passe en clair correspond à un mot de passe haché.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hache un mot de passe en clair.
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crée un jeton d'accès JWT.
    Args:
        data (dict): Les données à inclure dans le jeton (claims).
        expires_delta (timedelta, optional): Durée de validité du jeton. Si None, utilise la durée par défaut.
    Returns:
        str: Le jeton JWT encodé.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """
    Décode et valide un jeton d'accès JWT.
    Args:
        token (str): Le jeton JWT à décoder.
    Returns:
        dict: Les données (claims) contenues dans le jeton.
    Raises:
        UnauthorizedException: Si le jeton est invalide, expiré ou malformé.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Vous pouvez ajouter des vérifications supplémentaires sur le payload ici si nécessaire
        return payload
    except JWTError as e:
        logger.warning(f"Erreur de décodage ou de validation JWT: {e}")
        raise UnauthorizedException(detail="Jeton invalide ou expiré.")
    except Exception as e:
        logger.error(f"Erreur inattendue lors du décodage du jeton: {e}", exc_info=True)
        raise UnauthorizedException(detail="Jeton malformé ou erreur interne.")

