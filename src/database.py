"""Database models and session helpers for the local application."""
from __future__ import annotations

import os
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session

from src.config import SQLITE_DATABASE_PATH

DATABASE_URL = os.getenv("CATFISH_DATABASE_URL", f"sqlite:///{SQLITE_DATABASE_PATH}")
DATABASE_URL_CONFIGURED = bool(os.getenv("CATFISH_DATABASE_URL"))
logger = logging.getLogger(__name__)


class DatabaseUnavailableError(RuntimeError):
    """Raised when the configured database cannot be used safely."""


@dataclass(frozen=True)
class DatabaseDiagnostic:
    configured: bool
    dialect: Optional[str]
    hostname_resolves: Optional[bool]
    status: str
    message: str


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


if DATABASE_URL.startswith("sqlite"):
    try:
        engine: Optional[Engine] = create_engine(DATABASE_URL, future=True, pool_pre_ping=True, **_sqlite_args())
        _engine_configuration_error: Optional[Exception] = None
    except (SQLAlchemyError, ValueError, ImportError) as exc:
        engine = None
        _engine_configuration_error = exc
else:
    # Do not raise during Streamlit module import: app.py renders a controlled
    # configuration-conflict page below. The SQLite prototype never connects
    # to external databases or silently substitutes a different store.
    engine = None
    _engine_configuration_error = None

# SQLite does not enforce declared foreign keys unless each connection enables it.
# This listener is intentionally registered before any session is created.
if engine is not None and DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)


def database_diagnostic() -> DatabaseDiagnostic:
    """Return a safe SQLite-prototype health summary without sensitive details."""
    if not DATABASE_URL.startswith("sqlite"):
        return DatabaseDiagnostic(
            True,
            None,
            None,
            "external_database_configured",
            "This SQLite prototype cannot start while CATFISH_DATABASE_URL selects an external database. Remove that secret and restart the app.",
        )
    if _engine_configuration_error is not None:
        return DatabaseDiagnostic(DATABASE_URL_CONFIGURED, "sqlite", None, "invalid_sqlite_url", "The SQLite database URL is invalid.")
    return DatabaseDiagnostic(DATABASE_URL_CONFIGURED, "sqlite", None, "ready", "SQLite database configuration is available.")


def init_database() -> None:
    diagnostic = database_diagnostic()
    if diagnostic.status != "ready":
        logger.warning("Database startup unavailable: status=%s dialect=%s dns=%s", diagnostic.status, diagnostic.dialect, diagnostic.hostname_resolves)
        raise DatabaseUnavailableError(diagnostic.message)
    if DATABASE_URL.startswith("sqlite:///"):
        database_path = DATABASE_URL.removeprefix("sqlite:///")
        if database_path != ":memory:":
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    try:
        if engine is None:
            raise DatabaseUnavailableError("The database engine is unavailable.")
        Base.metadata.create_all(engine)
    except SQLAlchemyError as exc:
        logger.warning("SQLite schema startup unavailable")
        raise DatabaseUnavailableError("The SQLite database could not be initialized.") from exc


@contextmanager
def session_scope() -> Iterator[Session]:
    if engine is None:
        raise DatabaseUnavailableError("The database engine is unavailable.")
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
