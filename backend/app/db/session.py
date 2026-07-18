"""SQLite and SQLModel session lifecycle utilities."""

from pathlib import Path

from sqlmodel import SQLModel, Session, create_engine

from app.core.config import get_settings


settings = get_settings()


def _ensure_sqlite_directory(database_url: str) -> None:
    """Create the parent directory for a file-backed SQLite database."""
    prefix = "sqlite:///"
    if not database_url.startswith(prefix) or database_url == "sqlite:///:memory:":
        return

    database_path = database_url.removeprefix(prefix)
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_directory(settings.database_url)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
)


def create_db_and_tables() -> None:
    """Create registered SQLModel tables during application startup."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Yield a SQLModel session for future route dependencies."""
    with Session(engine) as session:
        yield session
