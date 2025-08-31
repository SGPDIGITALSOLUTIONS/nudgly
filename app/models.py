"""SQLAlchemy models for Nudgly application."""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

from .settings import DATABASE_URL

Base = declarative_base()


class ReminderStatus(str, Enum):
    """Status of a reminder."""
    PENDING = "PENDING"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class ReminderSource(str, Enum):
    """Source of how the reminder was created."""
    TEXT = "text"
    VOICE = "voice"


class Reminder(Base):
    """Reminder model for storing user reminders."""
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    created_by = Column(String(50), nullable=False, index=True)  # E.164 format: whatsapp:+447...
    for_user = Column(String(50), nullable=False, index=True)    # Usually Natasha's number
    text = Column(Text, nullable=False)                          # The reminder text
    due_at = Column(DateTime, nullable=False, index=True)        # When reminder is due (UTC)
    recurrence = Column(String(50), nullable=True)              # e.g., DAILY, WEEKLY:MO
    status = Column(String(20), nullable=False, default=ReminderStatus.PENDING)
    source = Column(String(10), nullable=False, default=ReminderSource.TEXT)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Reminder(id={self.id}, text='{self.text[:30]}...', due_at={self.due_at})>"


class Contact(Base):
    """Contact model for managing trusted users."""
    __tablename__ = "contacts"

    phone = Column(String(50), primary_key=True)  # E.164 format: whatsapp:+447...
    name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)     # owner, family, etc.
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Contact(phone='{self.phone}', name='{self.name}', role='{self.role}')>"


# Database engine and session setup
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

