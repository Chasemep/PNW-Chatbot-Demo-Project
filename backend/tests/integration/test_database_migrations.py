import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from app.core.config import get_settings
from sqlalchemy import create_engine, inspect

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_CONFIG = BACKEND_ROOT / "alembic.ini"


def alembic_config(database_url: str) -> Config:
    os.environ["DATABASE_URL"] = database_url
    get_settings.cache_clear()
    config = Config(str(ALEMBIC_CONFIG))
    config.set_main_option("script_location", str(BACKEND_ROOT / "app/db/migrations"))
    return config


def test_migrations_upgrade_and_downgrade(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'migration.db'}"
    config = alembic_config(database_url)

    command.upgrade(config, "head")
    engine = create_engine(database_url)
    inspector = inspect(engine)
    expected_tables = {
        "alembic_version",
        "approved_sources",
        "knowledge_base_releases",
        "source_content_segments",
        "student_questions",
        "grounded_answers",
        "answer_citations",
        "safe_referrals",
        "parsing_review_records",
        "preparation_validations",
    }
    assert expected_tables <= set(inspector.get_table_names())
    assert "embedding" in {
        column["name"]
        for column in inspector.get_columns("source_content_segments")
    }

    command.downgrade(config, "base")
    assert set(inspect(engine).get_table_names()) == {"alembic_version"}

    command.upgrade(config, "head")
    assert "approved_sources" in inspect(engine).get_table_names()
    engine.dispose()
