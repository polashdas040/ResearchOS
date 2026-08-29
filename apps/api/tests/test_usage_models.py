from pathlib import Path

from apps.api.app.db.models.usage import ModelUsageEventRecord

ROOT = Path(__file__).resolve().parents[3]


def test_model_usage_event_model_exists() -> None:
    columns = set(ModelUsageEventRecord.__table__.columns.keys())

    assert {"provider_name", "model_name", "total_tokens", "conversation_id"} <= columns


def test_model_usage_migration_exists() -> None:
    migration = ROOT / "migrations" / "versions" / "20260825_0003_model_usage_events.py"

    assert migration.exists()
    assert "model_usage_events" in migration.read_text()
