# Fichier placeholder pour env.py
# backend/persistence-service/migrations/env.py

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine

from alembic import context

# Importe la base déclarative de notre application
from ..database import Base
# Importe les modèles ORM pour qu'Alembic puisse les découvrir
from ..models import (
    User, Project, Document, DocumentVersion, ContentBlock, Exercise, WorkflowTask, UserFeedback,
    MathematicalConcept, ConceptDefinition, ConceptProperty, Theorem,
    PedagogicalPitfall, PedagogicalAnalogy, ConceptApplication, HistoricalNote,
    ConceptPrerequisite, ConceptTheoremRelation
)
from shared.config import get_settings # Importe notre configuration partagée

# Charge la configuration de logging depuis le fichier alembic.ini
fileConfig(context.config.config_file_name)

# Récupère le logger
import logging
logger = logging.getLogger(__name__)

# Récupère l'objet de configuration d'Alembic
config = context.config

# Récupère les paramètres de notre application
settings = get_settings()

# Définit la cible des métadonnées pour Alembic
# C'est ici qu'Alembic trouvera tous les modèles SQLAlchemy que nous avons définis
target_metadata = Base.metadata

# Section pour la configuration des URL de base de données
def get_url():
    """Récupère l'URL de la base de données à partir de nos paramètres."""
    # Alembic peut être exécuté dans un environnement où DATABASE_URL est déjà défini
    # ou nous pouvons le passer via alembic.ini ou une variable d'environnement.
    # Nous utilisons notre get_settings() pour la cohérence.
    return settings.DATABASE_URL

def run_migrations_offline():
    """
    Exécute les migrations en mode "offline".
    Dans ce mode, Alembic ne se connecte pas à la base de données.
    Il génère le SQL des migrations.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    """
    Exécute les migrations en mode "online".
    Dans ce mode, Alembic se connecte à la base de données et applique les migrations.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Pour les bases de données asynchrones, nous devons spécifier un dialecte
        # qui supporte l'exécution asynchrone.
        # SQLAlchemy 2.0+ le gère mieux automatiquement, mais c'est une bonne pratique.
        dialect_name="postgresql+asyncpg", # Utilise le driver asyncpg pour PostgreSQL asynchrone
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    """
    Exécute les migrations en mode "online" pour une base de données asynchrone.
    """
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            url=get_url(), # Utilise notre fonction pour obtenir l'URL
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

if context.is_offline_mode():
    run_migrations_offline()
else:
    # Pour le mode online, nous devons exécuter la fonction asynchrone
    # dans un événement loop.
    import asyncio
    asyncio.run(run_migrations_online())

