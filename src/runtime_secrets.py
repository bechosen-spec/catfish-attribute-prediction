"""Read deployment secrets without making application logic depend on one host."""
from __future__ import annotations

import os
from typing import Mapping, Optional


def read_secret(name: str, streamlit_secrets: Optional[Mapping[str, object]] = None) -> Optional[str]:
    """Prefer environment variables, then root-level Streamlit Secrets values."""
    value = os.getenv(name)
    if value is not None:
        return value
    if streamlit_secrets is None:
        return None
    value = streamlit_secrets.get(name)
    return value if isinstance(value, str) else None
