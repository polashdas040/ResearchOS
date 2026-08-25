from pathlib import Path

from apps.api.app.db.models.projects import ConversationRecord, MessageRecord, ProjectRecord

ROOT = Path(__file__).resolve().parents[3]


def test_project_conversation_message_models_exist() -> None:
    assert "organization_id" in ProjectRecord.__table__.columns
    assert "project_id" in ConversationRecord.__table__.columns
    assert "message_type" in MessageRecord.__table__.columns


def test_project_conversation_migration_exists() -> None:
    migration = ROOT / "migrations" / "versions" / "20260825_0002_projects_conversations.py"

    assert migration.exists()
    text = migration.read_text()
    assert "projects" in text
    assert "conversations" in text
    assert "messages" in text
