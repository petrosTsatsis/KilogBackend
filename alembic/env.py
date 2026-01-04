import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy import pool

# -----------------------------------------------------------
# 1. SETUP PYTHON PATH
# -----------------------------------------------------------
# This allows Alembic to see your 'app' folder when running inside Docker
sys.path.append(os.getcwd())

# -----------------------------------------------------------
# 2. IMPORT MODELS
# -----------------------------------------------------------
# Import your Base and all Models so Alembic can detect tables
from app.database import Base

# -----------------------------------------------------------
# 3. CONFIGURATION
# -----------------------------------------------------------
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Point to your model's metadata
target_metadata = Base.metadata


# -----------------------------------------------------------
# 4. GET DB URL FUNCTION
# -----------------------------------------------------------
def get_url():
    """
    Reads the database URL from the environment variable.
    This is critical for Docker/Supabase connectivity.
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable is not set.")
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()  # <--- Use our dynamic URL function
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    # Inject the URL into the config object so SQLAlchemy uses it
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()  # <--- Overwrite ini value

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
