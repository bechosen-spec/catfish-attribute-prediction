"""Root-level Streamlit Secrets resolution can be tested without a deployment."""
from src.runtime_secrets import read_secret


def test_streamlit_style_secret_mapping_is_used_when_environment_is_absent(monkeypatch):
    monkeypatch.delenv("CATFISH_ADMIN_EMAIL", raising=False)
    assert read_secret("CATFISH_ADMIN_EMAIL", {"CATFISH_ADMIN_EMAIL": "admin@example.com"}) == "admin@example.com"


def test_environment_takes_precedence_over_streamlit_mapping(monkeypatch):
    monkeypatch.setenv("CATFISH_ADMIN_EMAIL", "environment@example.com")
    assert read_secret("CATFISH_ADMIN_EMAIL", {"CATFISH_ADMIN_EMAIL": "streamlit@example.com"}) == "environment@example.com"


def test_missing_or_non_string_secret_is_not_accepted(monkeypatch):
    monkeypatch.delenv("CATFISH_ADMIN_EMAIL", raising=False)
    assert read_secret("CATFISH_ADMIN_EMAIL", {}) is None
    assert read_secret("CATFISH_ADMIN_EMAIL", {"CATFISH_ADMIN_EMAIL": 1}) is None
