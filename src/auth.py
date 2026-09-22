"""Credential validation and trusted server-side authentication operations."""
from __future__ import annotations
import re
from datetime import timedelta
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from src.database import AdminAuditLog, User, utcnow

PASSWORD_HASHER = PasswordHasher()
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

class AuthError(ValueError): pass

def register(session, full_name: str, username: str, email: str, password: str, confirmation: str) -> User:
    full_name, username, email = full_name.strip(), username.strip(), email.strip().lower()
    if not full_name or not username or len(username) > 64 or not re.fullmatch(r"[A-Za-z0-9_.-]+", username): raise AuthError("Enter a valid username (letters, numbers, dot, underscore, or hyphen).")
    if not EMAIL_RE.fullmatch(email): raise AuthError("Enter a valid email address.")
    if len(password) < 8: raise AuthError("Password must contain at least 8 characters.")
    if password != confirmation: raise AuthError("Passwords do not match.")
    if session.scalar(select(User).where(User.username == username)): raise AuthError("That username is already in use.")
    if session.scalar(select(User).where(User.email == email)): raise AuthError("That email address is already in use.")
    user = User(full_name=full_name, username=username, email=email, password_hash=PASSWORD_HASHER.hash(password), role="USER")
    session.add(user); session.flush(); return user

def authenticate(session, identifier: str, password: str) -> User:
    user = session.scalar(select(User).where(or_(User.username == identifier.strip(), User.email == identifier.strip().lower())))
    if not user or not user.is_active: raise AuthError("Invalid credentials or disabled account.")
    try: PASSWORD_HASHER.verify(user.password_hash, password)
    except VerifyMismatchError as exc: raise AuthError("Invalid credentials or disabled account.") from exc
    user.last_login_at = utcnow(); return user

def change_password(user: User, current: str, new: str, confirmation: str) -> None:
    try: PASSWORD_HASHER.verify(user.password_hash, current)
    except VerifyMismatchError as exc: raise AuthError("Current password is incorrect.") from exc
    if len(new) < 8: raise AuthError("New password must contain at least 8 characters.")
    if new != confirmation: raise AuthError("Passwords do not match.")
    user.password_hash = PASSWORD_HASHER.hash(new); user.must_change_password = False

def create_initial_admin(session, password: str, email: str) -> User:
    if session.scalar(select(User).where(User.role == "ADMIN")): raise AuthError("An administrator account already exists.")
    if len(password) < 8: raise AuthError("CATFISH_ADMIN_INITIAL_PASSWORD must be at least 8 characters.")
    email = email.strip().lower()
    if not EMAIL_RE.fullmatch(email): raise AuthError("Enter a valid administrator email address.")
    admin = User(full_name="System Administrator", username="admin", email=email, password_hash=PASSWORD_HASHER.hash(password), role="ADMIN", must_change_password=True)
    session.add(admin); session.flush(); return admin


def promote_user_to_admin(session, email: str, actor: User | None = None) -> User:
    """Promote one existing account without changing its credentials or records."""
    email = email.strip().lower()
    if not EMAIL_RE.fullmatch(email):
        raise AuthError("Enter a valid email address.")
    matches = list(session.scalars(select(User).where(User.email == email)))
    if not matches:
        raise AuthError("No account exists for that email address.")
    if len(matches) != 1:
        raise AuthError("More than one account matched that email address; promotion stopped.")
    user = matches[0]
    if user.role == "ADMIN":
        return user
    user.role = "ADMIN"
    if actor is not None:
        if actor.role != "ADMIN" or not actor.is_active:
            raise AuthError("Audit actor must be an active administrator.")
        session.add(AdminAuditLog(
            admin_user_id=actor.id,
            action="user_promoted_to_admin",
            target_type="user",
            target_id=str(user.id),
            details=f"Promoted {user.email} using the trusted operator script.",
        ))
    session.flush()
    return user
