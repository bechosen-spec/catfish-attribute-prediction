from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.auth import create_initial_admin
from src.database import Base


def test_initial_admin_is_forced_to_change_password():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    admin = create_initial_admin(session, "qa-initial-password", "admin@example.com")
    assert admin.role == "ADMIN"
    assert admin.must_change_password is True
