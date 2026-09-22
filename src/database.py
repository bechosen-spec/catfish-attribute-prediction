"""Database models and session helpers for the local application."""
from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session

from src.config import ROOT_DIR

DATABASE_URL = os.getenv("CATFISH_DATABASE_URL", f"sqlite:///{ROOT_DIR / 'data' / 'catfish.db'}")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="USER", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    experiments: Mapped[list["Experiment"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class ModelVersion(Base):
    __tablename__ = "model_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identifier: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class Experiment(Base):
    __tablename__ = "experiments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="PROCESSING", index=True)
    image_path: Mapped[Optional[str]] = mapped_column(String(512))
    processing_ms: Mapped[Optional[int]] = mapped_column(Integer)
    owner: Mapped[User] = relationship(back_populates="experiments")
    validation: Mapped[Optional["ImageValidationResult"]] = relationship(back_populates="experiment", uselist=False, cascade="all, delete-orphan")
    prediction: Mapped[Optional["PredictionResultRecord"]] = relationship(back_populates="experiment", uselist=False, cascade="all, delete-orphan")


class ImageValidationResult(Base):
    __tablename__ = "image_validation_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, unique=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_fish: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    detected_label: Mapped[str] = mapped_column(String(128), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    experiment: Mapped[Experiment] = relationship(back_populates="validation")


class PredictionResultRecord(Base):
    __tablename__ = "prediction_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, unique=True)
    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_versions.id"), nullable=False)
    growth_stage: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    probabilities_json: Mapped[str] = mapped_column(Text, nullable=False)
    standard_length_cm: Mapped[float] = mapped_column(Float, nullable=False)
    total_length_cm: Mapped[float] = mapped_column(Float, nullable=False)
    weight_g: Mapped[float] = mapped_column(Float, nullable=False)
    experiment: Mapped[Experiment] = relationship(back_populates="prediction")
    model_version: Mapped[ModelVersion] = relationship()


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(96), nullable=False)
    target_type: Mapped[str] = mapped_column(String(48), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


def _sqlite_args() -> dict:
    return {"connect_args": {"check_same_thread": False}} if DATABASE_URL.startswith("sqlite") else {}


engine = create_engine(DATABASE_URL, future=True, **_sqlite_args())

# SQLite does not enforce declared foreign keys unless each connection enables it.
# This listener is intentionally registered before any session is created.
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)


def init_database() -> None:
    if DATABASE_URL.startswith("sqlite"):
        Path(DATABASE_URL.removeprefix("sqlite:///" )).parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
