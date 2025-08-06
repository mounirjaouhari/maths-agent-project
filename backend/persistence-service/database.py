# Fichier placeholder pour database.py
# backend/persistence-service/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import text # Importe text pour les requêtes brutes si nécessaire
import logging

from shared.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Création de l'engine SQLAlchemy pour la connexion asynchrone
# create_async_engine est utilisé pour les drivers asynchrones (ex: asyncpg via psycopg2)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG_MODE, # Affiche les requêtes SQL dans les logs si en mode debug
    pool_size=10, # Taille du pool de connexions
    max_overflow=20 # Nombre de connexions supplémentaires autorisées au-delà de pool_size
)

# Création d'une session locale asynchrone
# expire_on_commit=False est important pour ne pas invalider les objets après un commit
AsyncSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Base déclarative pour les modèles ORM SQLAlchemy
Base = declarative_base()

async def init_db():
    """
    Initialise la base de données en créant toutes les tables définies dans les modèles.
    Cette fonction est principalement utilisée pour le développement local ou les tests.
    En production, les migrations Alembic devraient gérer la création et la mise à jour du schéma.
    """
    async with engine.begin() as conn:
        # Exécute la création des tables de manière synchrone sur la connexion asynchrone
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Base de données initialisée : tables créées si non existantes.")

async def get_db():
    """
    Dépendance FastAPI pour obtenir une session de base de données pour chaque requête.
    Gère l'ouverture et la fermeture de la session.
    """
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()

