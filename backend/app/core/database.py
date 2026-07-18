"""SQLAlchemy database infrastructure shared by future application modules."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, text
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


def initialize_database() -> None:
    """Create application tables and verify the database connection."""
    import app.models  # noqa: F401 - registers all model metadata before creation

    Base.metadata.create_all(bind=engine)
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session for future dependency injection."""
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()
