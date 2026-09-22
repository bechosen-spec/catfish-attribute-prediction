"""Database/authentication tests; use a temporary SQLite database via fixtures."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
from src.auth import AuthError, authenticate, register
from src.database import Base

@pytest.fixture
def session():
    engine=create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    s=sessionmaker(bind=engine)()
    yield s
    s.close()

def test_register_and_login(session):
    user=register(session,"A User","auser","a@example.com","strong-pass","strong-pass"); session.commit()
    assert authenticate(session,"auser","strong-pass").id==user.id

def test_duplicate_username_and_weak_password_rejected(session):
    register(session,"A User","auser","a@example.com","strong-pass","strong-pass")
    with pytest.raises(AuthError,match="username"): register(session,"Other","auser","b@example.com","strong-pass","strong-pass")
    with pytest.raises(AuthError,match="least 8"): register(session,"Other","other","b@example.com","short","short")

def test_disabled_user_cannot_login(session):
    user=register(session,"A User","auser","a@example.com","strong-pass","strong-pass"); user.is_active=False; session.commit()
    with pytest.raises(AuthError): authenticate(session,"auser","strong-pass")
