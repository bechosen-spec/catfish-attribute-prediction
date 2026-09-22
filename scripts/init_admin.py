"""Explicitly create the first local administrator account."""
from __future__ import annotations
import os
import sys
from argparse import ArgumentParser
from pathlib import Path

# Permit ``python scripts/init_admin.py`` from a checkout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.auth import AuthError, create_initial_admin
from src.database import init_database, session_scope

def main() -> None:
    parser = ArgumentParser(description="Create the first administrator account.")
    parser.add_argument("--email", default=os.getenv("CATFISH_ADMIN_EMAIL"), help="Administrator email address (or set CATFISH_ADMIN_EMAIL).")
    args = parser.parse_args()
    password = os.getenv("CATFISH_ADMIN_INITIAL_PASSWORD")
    if not password:
        raise SystemExit("Set CATFISH_ADMIN_INITIAL_PASSWORD before running this command.")
    if not args.email:
        raise SystemExit("Pass --email or set CATFISH_ADMIN_EMAIL before running this command.")
    init_database()
    try:
        with session_scope() as session:
            create_initial_admin(session, password, args.email)
    except AuthError as exc:
        raise SystemExit(str(exc)) from exc
    print("Initial administrator created. Sign in as admin and change the initial password.")

if __name__ == "__main__": main()
