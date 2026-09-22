"""Safe database-startup diagnostics without a real external database."""
import src.database as database


def test_external_database_configuration_is_blocked_without_exposing_url(monkeypatch):
    monkeypatch.setattr(database, "DATABASE_URL", "postgresql+psycopg://operator:dontleak@missing.invalid:5432/app")
    result = database.database_diagnostic()
    assert result.status == "external_database_configured"
    assert "dontleak" not in result.message
    assert "operator" not in result.message


def test_default_database_is_sqlite():
    result = database.database_diagnostic()
    assert result.dialect == "sqlite"
    assert result.status == "ready"


def test_unavailable_engine_blocks_session_use(monkeypatch):
    monkeypatch.setattr(database, "engine", None)
    try:
        with database.session_scope():
            pass
    except database.DatabaseUnavailableError:
        return
    raise AssertionError("database session should not be created without an engine")
