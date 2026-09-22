"""Role-promotion tests use an isolated in-memory database."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

from src.auth import AuthError, authenticate, promote_user_to_admin, register
from src.database import AdminAuditLog, Base, Experiment


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    value = sessionmaker(bind=engine)()
    yield value
    value.close()


def test_promotion_preserves_password_login_and_experiments(session):
    member = register(session, "Member User", "member", "member@example.com", "strong-password", "strong-password")
    session.flush()
    experiment = Experiment(user_id=member.id, status="REJECTED")
    session.add(experiment)
    session.commit()
    original_hash = member.password_hash

    promoted = promote_user_to_admin(session, "MEMBER@EXAMPLE.COM")
    session.commit()

    assert promoted.id == member.id
    assert promoted.role == "ADMIN"
    assert promoted.password_hash == original_hash
    assert authenticate(session, "member@example.com", "strong-password").id == member.id
    assert session.get(Experiment, experiment.id).user_id == member.id


def test_nonexistent_user_cannot_be_promoted(session):
    with pytest.raises(AuthError, match="No account exists"):
        promote_user_to_admin(session, "nobody@example.com")


def test_duplicate_promotion_is_a_safe_noop(session):
    member = register(session, "Member User", "member", "member@example.com", "strong-password", "strong-password")
    session.commit()
    promote_user_to_admin(session, member.email)
    session.commit()

    again = promote_user_to_admin(session, member.email)
    assert again.role == "ADMIN"


def test_promotion_records_audit_log_when_active_admin_actor_is_supplied(session):
    actor = register(session, "Admin User", "operator", "operator@example.com", "strong-password", "strong-password")
    actor.role = "ADMIN"
    member = register(session, "Member User", "member", "member@example.com", "strong-password", "strong-password")
    session.commit()

    promote_user_to_admin(session, member.email, actor=actor)
    session.commit()
    audit = session.query(AdminAuditLog).one()
    assert audit.admin_user_id == actor.id
    assert audit.action == "user_promoted_to_admin"
    assert audit.target_id == str(member.id)


def test_non_admin_actor_cannot_be_used_for_audit_attribution(session):
    actor = register(session, "Other User", "other", "other@example.com", "strong-password", "strong-password")
    member = register(session, "Member User", "member", "member@example.com", "strong-password", "strong-password")
    session.commit()

    with pytest.raises(AuthError, match="active administrator"):
        promote_user_to_admin(session, member.email, actor=actor)
