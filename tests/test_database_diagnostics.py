"""Safe database-startup diagnostics without a real external database."""
import src.database as database


def test_diagnostic_does_not_expose_database_url(monkeypatch):
    monkeypatch.setattr(database, "DATABASE_URL", "postgresql+psycopg://user:secret@missing.invalid:5432/app")
    result = database.database_diagnostic()
    assert result.status == "dns_error"
    assert "secret" not in result.message
    assert "user" not in result.message


def test_failure_categories_are_safe():
    status, message = database._failure_status(Exception("password authentication failed"))
    assert status == "authentication_error"
    assert "password" not in message.lower()

    status, message = database._failure_status(Exception("SSL certificate verify failed"))
    assert status == "ssl_error"
    assert "certificate" not in message.lower()

    status, _ = database._failure_status(Exception("connection failed: unavailable"))
    assert status == "server_unavailable"


def test_unavailable_engine_blocks_session_use(monkeypatch):
    monkeypatch.setattr(database, "engine", None)
    try:
        with database.session_scope():
            pass
    except database.DatabaseUnavailableError:
        return
    raise AssertionError("database session should not be created without an engine")
