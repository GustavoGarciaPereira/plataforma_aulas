"""Conexão com o banco — engine, SessionLocal e dependência get_db().

PRD v1.0, seção 8: SQLAlchemy + psycopg2 (PostgreSQL síncrono).
A conexão é lazy: importar este módulo não exige o banco no ar.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings
from .models import Base  # noqa: F401  # registra os models no metadata (Alembic usa)

engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    """Dependência do FastAPI: fornece uma sessão e a fecha ao final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
