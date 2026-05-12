from backend.config.database_url import normalize_database_url, resolve_database_url


def test_normalize_render_postgres_url() -> None:
    assert normalize_database_url("postgresql://u:p@example.com/db") == "postgresql+psycopg://u:p@example.com/db"


def test_resolve_database_url_prefers_env(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@example.com/db")
    assert resolve_database_url() == "postgresql+psycopg://u:p@example.com/db"


def test_resolve_database_url_yaml_fallback(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    config = {
        "database": {"username": "u", "password": "p", "host": "h", "port": 5433},
        "tenants": {"default": {"database": {"name": "d"}}},
    }
    assert resolve_database_url(config) == "postgresql+psycopg://u:p@h:5433/d"
