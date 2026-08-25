from pathlib import Path

from apps.api.app.db.models.auth import RefreshTokenRecord, UserRecord

ROOT = Path(__file__).resolve().parents[3]


def test_auth_models_do_not_store_raw_passwords() -> None:
    user_columns = set(UserRecord.__table__.columns.keys())

    assert "password_hash" in user_columns
    assert "password" not in user_columns


def test_auth_migration_exists() -> None:
    migration = ROOT / "migrations" / "versions" / "20260825_0001_auth_tenant_security.py"

    assert migration.exists()
    assert "refresh_tokens" in migration.read_text()
    assert "memberships" in migration.read_text()
    assert "organizations" in migration.read_text()


def test_refresh_token_record_stores_fingerprint_only() -> None:
    token_columns = set(RefreshTokenRecord.__table__.columns.keys())

    assert "token_fingerprint" in token_columns
    assert "refresh_token" not in token_columns
