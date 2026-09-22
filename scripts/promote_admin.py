"""Promote one existing account through a trusted server-side operator session."""
from __future__ import annotations

import sys
from argparse import ArgumentParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.auth import AuthError, promote_user_to_admin
from src.database import User, init_database, session_scope


def _confirm() -> bool:
    return input("Type PROMOTE to confirm this role change: ").strip() == "PROMOTE"


def main() -> None:
    parser = ArgumentParser(description="Promote an existing user to administrator.")
    parser.add_argument("--email", required=True, help="Registered email address to promote.")
    parser.add_argument(
        "--actor-email",
        help="Optional active administrator email to attribute in the audit log. "
        "Omit only when no authenticated actor can be recorded.",
    )
    args = parser.parse_args()

    init_database()
    try:
        with session_scope() as session:
            matches = list(session.query(User).filter(User.email == args.email.strip().lower()))
            if not matches:
                raise AuthError("No account exists for that email address.")
            if len(matches) != 1:
                raise AuthError("More than one account matched that email address; promotion stopped.")
            user = matches[0]
            print(f"User ID: {user.id}")
            print(f"Full name: {user.full_name}")
            print(f"Username: {user.username}")
            print(f"Current role: {user.role}")
            print(f"Account active: {user.is_active}")
            if user.role == "ADMIN":
                print("No role change is necessary; this account is already an administrator.")
                return
            if not _confirm():
                raise SystemExit("Promotion cancelled; no changes were made.")
            actor = None
            if args.actor_email:
                actor = session.query(User).filter(User.email == args.actor_email.strip().lower()).one_or_none()
                if actor is None:
                    raise AuthError("No audit actor exists for that email address.")
            promote_user_to_admin(session, args.email, actor=actor)
    except AuthError as exc:
        raise SystemExit(str(exc)) from exc
    print("Promotion complete. The account password and history were preserved.")


if __name__ == "__main__":
    main()
