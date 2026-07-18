"""SQLAlchemy database infrastructure shared by future application modules."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


settings = get_settings()


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models introduced in future milestones."""


def _ensure_sqlite_parent(database_url: str) -> None:
    """Create the parent directory for a file-backed SQLite URL when needed."""
    prefix = "sqlite:///"
    if not database_url.startswith(prefix) or database_url == "sqlite:///:memory:":
        return

    database_path = Path(database_url.removeprefix(prefix))
    database_path.parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_parent(settings.database_url)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _migrate_sqlite_schema() -> None:
    """Add columns introduced after an existing local SQLite database was created.

    ``create_all`` only creates missing tables; it does not alter existing ones.
    These additive migrations keep local development databases compatible without
    discarding uploaded-report history.
    """
    if engine.dialect.name != "sqlite":
        return

    migrations = {
        "reports": {
            "updated_at": "DATETIME",
            "video_name": "VARCHAR(255)",
            "video_duration": "FLOAT",
            "processing_time": "FLOAT",
            "submission_status": "VARCHAR(32) NOT NULL DEFAULT 'NOT_SUBMITTED'",
            "reward_status": "VARCHAR(100)",
            "summary_json": "JSON NOT NULL DEFAULT '{}'",
        },
        # These fields were added after the first local database version.  Keep
        # their defaults compatible with the SQLAlchemy model so old incident
        # rows remain valid and new analysis runs can insert detections.
        "incidents": {
            "severity": "VARCHAR(50)",
            "approved": "BOOLEAN NOT NULL DEFAULT 0",
            "tracking_object": "VARCHAR(255)",
        },
    }

    with engine.begin() as connection:
        inspector = inspect(connection)
        tables = set(inspector.get_table_names())
        for table, columns in migrations.items():
            if table not in tables:
                continue
            existing_columns = {
                column["name"] for column in inspector.get_columns(table)
            }
            for name, definition in columns.items():
                if name not in existing_columns:
                    connection.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
                    )


def initialize_database() -> None:
    """Create application tables and verify the database connection."""
    import app.models  # noqa: F401 - registers all model metadata before creation

    Base.metadata.create_all(bind=engine)
    _migrate_sqlite_schema()
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session for future dependency injection."""
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()
