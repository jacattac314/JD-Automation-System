"""
Database layer using SQLAlchemy ORM.

Provides models for Users, Runs, and API usage tracking.
Supports SQLite for development and PostgreSQL for production.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean,
    DateTime, Text, JSON, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from loguru import logger

from core.settings import settings

Base = declarative_base()


# ============ Models ============

class User(Base):
    """Application user (authenticated via GitHub OAuth)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    github_id = Column(Integer, unique=True, nullable=False, index=True)
    github_username = Column(String(255), unique=True, nullable=False)
    github_avatar_url = Column(String(500), nullable=True)
    email = Column(String(255), nullable=True)
    github_token_encrypted = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    runs = relationship("Run", back_populates="user", lazy="dynamic")
    api_usage = relationship("ApiUsage", back_populates="user", lazy="dynamic")

    __table_args__ = (
        Index("idx_user_github_id", "github_id"),
        Index("idx_user_github_username", "github_username"),
    )


class Run(Base):
    """A single pipeline execution."""
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Input
    app_idea = Column(Text, nullable=False)
    tech_preferences = Column(Text, nullable=True)

    # Output
    status = Column(String(50), default="pending", nullable=False)
    project_title = Column(String(255), nullable=True)
    enhanced_idea = Column(JSON, nullable=True)
    prd_data = Column(JSON, nullable=True)
    prd_markdown = Column(Text, nullable=True)

    # GitHub
    repo_name = Column(String(255), nullable=True)
    repo_url = Column(String(500), nullable=True)
    repo_full_name = Column(String(500), nullable=True)

    # Metrics
    epics_count = Column(Integer, default=0)
    features_count = Column(Integer, default=0)
    features_completed = Column(Integer, default=0)
    implementation_mode = Column(String(50), nullable=True)
    elapsed_time = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="runs")

    __table_args__ = (
        Index("idx_run_user_id", "user_id"),
        Index("idx_run_status", "status"),
        Index("idx_run_created_at", "created_at"),
    )


class ApiUsage(Base):
    """Track API usage per user for rate limiting and billing."""
    __tablename__ = "api_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(String(10), nullable=False)  # YYYY-MM-DD for daily aggregation
    runs_count = Column(Integer, default=0)
    gemini_calls = Column(Integer, default=0)
    claude_minutes = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="api_usage")

    __table_args__ = (
        Index("idx_api_usage_user_date", "user_id", "date", unique=True),
    )


# ============ Engine & Session ============

engine = create_engine(
    settings.database_url,
    echo=(settings.log_level == "DEBUG"),
    pool_pre_ping=True,
    # SQLite-specific settings
    **({"connect_args": {"check_same_thread": False}} if "sqlite" in settings.database_url else {})
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables. Call on application startup."""
    Base.metadata.create_all(bind=engine)
    logger.info(f"Database initialized: {settings.database_url.split('?')[0]}")


def get_db() -> Session:
    """Get a database session. Use as a context manager or FastAPI dependency."""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


# ============ Repository Helpers ============

def get_or_create_user(db: Session, github_id: int, github_username: str,
                       avatar_url: Optional[str] = None, email: Optional[str] = None) -> User:
    """Get existing user or create a new one."""
    user = db.query(User).filter(User.github_id == github_id).first()
    if user:
        # Update profile info
        user.github_username = github_username
        if avatar_url:
            user.github_avatar_url = avatar_url
        if email:
            user.email = email
        user.updated_at = datetime.utcnow()
        db.commit()
        return user

    user = User(
        github_id=github_id,
        github_username=github_username,
        github_avatar_url=avatar_url,
        email=email,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def save_run(db: Session, run: Run) -> Run:
    """Save or update a run record."""
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_user_runs(db: Session, user_id: int, limit: int = 50, offset: int = 0):
    """Get runs for a specific user, newest first."""
    return (
        db.query(Run)
        .filter(Run.user_id == user_id)
        .order_by(Run.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_daily_usage(db: Session, user_id: int, date: str) -> Optional[ApiUsage]:
    """Get API usage for a user on a specific date."""
    return (
        db.query(ApiUsage)
        .filter(ApiUsage.user_id == user_id, ApiUsage.date == date)
        .first()
    )


def increment_usage(db: Session, user_id: int, runs: int = 0,
                    gemini_calls: int = 0, claude_minutes: float = 0.0):
    """Increment usage counters for today."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    usage = get_daily_usage(db, user_id, today)

    if usage:
        usage.runs_count += runs
        usage.gemini_calls += gemini_calls
        usage.claude_minutes += claude_minutes
    else:
        usage = ApiUsage(
            user_id=user_id,
            date=today,
            runs_count=runs,
            gemini_calls=gemini_calls,
            claude_minutes=claude_minutes,
        )
        db.add(usage)

    db.commit()
    return usage
