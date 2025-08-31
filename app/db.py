"""Database utilities and session management."""

from contextlib import contextmanager
from sqlalchemy.orm import Session
from .models import SessionLocal, create_tables, engine


def init_db():
    """Initialize the database by creating all tables."""
    create_tables()


@contextmanager
def get_db_session():
    """Context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

