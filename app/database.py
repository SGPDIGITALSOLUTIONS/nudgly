"""
Database configuration for cloud deployment.
Handles both local SQLite and cloud database connections.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .settings import DATABASE_URL

# For Vercel/cloud deployment, we need to handle database differently
def get_database_url():
    """Get database URL with cloud-specific handling."""
    if os.getenv("VERCEL"):
        # In Vercel, use a cloud database or in-memory for demo
        postgres_url = os.getenv("POSTGRES_URL")
        if postgres_url:
            return postgres_url
        else:
            # Fallback to in-memory SQLite for demo (not persistent)
            return "sqlite:///:memory:"
    else:
        # Local development
        return DATABASE_URL

# Create engine with cloud-appropriate settings
database_url = get_database_url()

if database_url.startswith("sqlite"):
    # SQLite settings
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if "memory" not in database_url else {}
    )
else:
    # PostgreSQL/other cloud database settings
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=300
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables."""
    # Import models to ensure they're registered
    from . import models
    Base.metadata.create_all(bind=engine)
