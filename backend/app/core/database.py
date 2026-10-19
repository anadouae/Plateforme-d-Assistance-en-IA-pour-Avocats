from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


def _database_url() -> str:
    """Force psycopg2 (installé) — SQLAlchemy récent peut résoudre postgresql:// → psycopg v3."""
    url = (settings.DATABASE_URL or "").strip()
    if url.startswith("sqlite"):
        return url
    if url.startswith("postgresql+psycopg://"):
        return "postgresql+psycopg2://" + url[len("postgresql+psycopg://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + url[len("postgresql://") :]
    return url


_db_url = _database_url()
connect_args = {"check_same_thread": False} if _db_url.startswith("sqlite") else {}
# pool_pre_ping évite les connexions mortes ; pool plus large pour éviter QueuePool timeout
# (ex. page Équipe bloquée en spinner pendant que le topbar poll /api/team/requests).
_engine_kwargs: dict = {"connect_args": connect_args}
if not _db_url.startswith("sqlite"):
    _engine_kwargs.update(
        pool_size=20,
        max_overflow=40,
        pool_pre_ping=True,
        pool_recycle=1800,
    )
engine = create_engine(_db_url, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
