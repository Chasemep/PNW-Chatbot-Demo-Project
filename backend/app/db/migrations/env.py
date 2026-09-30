"""Alembic migration environment."""

from logging.config import fileConfig
from typing import Any

from alembic import context
from pgvector.sqlalchemy import VECTOR
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.models import answer_log, review_record, source, source_chunk  # noqa: F401
from app.models.base import Base

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import model modules above so every table is registered on the shared metadata.
target_metadata = Base.metadata


def compare_type(
    _context: Any,
    _inspected_column: Any,
    _metadata_column: Any,
    _inspected_type: Any,
    metadata_type: Any,
) -> bool | None:
    """Ignore SQLite's NUMERIC reflection for PostgreSQL vector columns."""

    if _context.dialect.name == "sqlite" and isinstance(metadata_type, VECTOR):
        return False
    return None


def run_migrations_offline() -> None:
    """Run migrations without creating a database connection."""

    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        compare_type=compare_type,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using an engine created from application settings."""

    connectable = engine_from_config(
        {"sqlalchemy.url": get_settings().database_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=compare_type,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
