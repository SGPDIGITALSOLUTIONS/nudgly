"""Database utilities and session management."""

from contextlib import contextmanager
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base, init_db as init_database
from . import models


def init_db():
    """Initialize the database by creating all tables."""
    init_database()


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

