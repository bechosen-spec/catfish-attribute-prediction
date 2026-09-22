"""Secret-driven first-admin setup for the disposable SQLite Streamlit demo."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

from src.auth import (
    AuthError,
    authenticate,
    change_password,
    initialize_configured_admin,
    register,
)
from src.database import Base, User
from src.runtime_secrets import read_secret


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_configured_admin_is_created_once_and_can_log_in_after_password_change():
    session = _session()
    result = initialize_configured_admin(session, "ADMIN@example.com", "strong-initial-password")
    session.commit()
    admin = session.query(User).filter_by(username="admin").one()
    original_hash = admin.password_hash

    assert result.status == "created"
    assert admin.email == "admin@example.com"
    assert admin.role == "ADMIN"
    assert admin.must_change_password is True
    assert authenticate(session, "admin", "strong-initial-password").id == admin.id

    change_password(admin, "strong-initial-password", "strong-new-password", "strong-new-password")
    session.commit()
    assert admin.must_change_password is False
    assert authenticate(session, "admin@example.com", "strong-new-password").role == "ADMIN"
    with pytest.raises(AuthError):
        authenticate(session, "admin", "strong-initial-password")

    again = initialize_configured_admin(session, "admin@example.com", "different-strong-password")
    session.commit()
    assert again.status == "already_initialized"
    assert session.query(User).filter_by(username="admin").one().password_hash != original_hash


def test_streamlit_style_secrets_create_the_configured_admin(monkeypatch):
    monkeypatch.delenv("CATFISH_ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("CATFISH_ADMIN_INITIAL_PASSWORD", raising=False)
    secrets = {
        "CATFISH_ADMIN_EMAIL": "cloud-admin@example.com",
        "CATFISH_ADMIN_INITIAL_PASSWORD": "streamlit-strong-password",
    }
    session = _session()

    result = initialize_configured_admin(
        session,
        read_secret("CATFISH_ADMIN_EMAIL", secrets),
        read_secret("CATFISH_ADMIN_INITIAL_PASSWORD", secrets),
    )
    session.commit()

    assert result.status == "created"
    assert authenticate(session, "admin", "streamlit-strong-password").email == "cloud-admin@example.com"


def test_bootstrap_never_promotes_or_overwrites_existing_user():
    session = _session()
    member = register(session, "Existing User", "member", "member@example.com", "strong-password", "strong-password")
    session.commit()
    original_hash = member.password_hash

    result = initialize_configured_admin(session, "member@example.com", "different-strong-password")
    session.commit()

    assert result.status == "email_conflict"
    unchanged = session.get(User, member.id)
    assert unchanged.role == "USER"
    assert unchanged.password_hash == original_hash
    assert session.query(User).filter_by(username="admin").count() == 0


def test_bootstrap_requires_complete_strong_configuration():
    session = _session()
    assert initialize_configured_admin(session, None, None).status == "not_configured"
    assert initialize_configured_admin(session, "admin@example.com", None).status == "incomplete_configuration"
    assert initialize_configured_admin(session, "invalid-email", "strong-password").status == "invalid_email"
    assert initialize_configured_admin(session, "admin@example.com", "short").status == "weak_password"
    assert session.query(User).count() == 0
