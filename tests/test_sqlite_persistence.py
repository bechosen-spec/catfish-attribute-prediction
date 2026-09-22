"""File-backed SQLite persistence tests for the client-testing prototype."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.auth import authenticate, create_initial_admin, register
from src.database import Base, Experiment


def test_sqlite_file_preserves_accounts_admin_and_history_after_reopen(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'prototype.db'}"
    first_engine = create_engine(database_url)
    Base.metadata.create_all(first_engine)
    first_session = sessionmaker(bind=first_engine)()
    user = register(first_session, "Test User", "tester", "tester@example.com", "strong-password", "strong-password")
    first_session.add(Experiment(user_id=user.id, status="REJECTED"))
    admin = create_initial_admin(first_session, "initial-admin-password", "admin@example.com")
    first_session.commit()
    user_id, admin_id = user.id, admin.id
    first_session.close()
    first_engine.dispose()

    second_engine = create_engine(database_url)
    second_session = sessionmaker(bind=second_engine)()
    assert authenticate(second_session, "tester@example.com", "strong-password").id == user_id
    assert second_session.get(type(admin), admin_id).role == "ADMIN"
    assert second_session.query(Experiment).filter_by(user_id=user_id).count() == 1
    second_session.close()
