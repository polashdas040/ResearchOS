from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.app.db.base import Base
from apps.api.app.db.models.auth import OrganizationRecord, UserRecord
from apps.api.app.domain.conversations.models import MessageType
from apps.api.app.repositories.projects import SqlAlchemyProjectRepository


@pytest.mark.asyncio
async def test_sqlalchemy_project_repository_persists_project_conversation_and_message() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    organization_id = uuid4()
    user_id = uuid4()
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(OrganizationRecord(id=organization_id, name="SQLite Lab", created_at=_now()))
        session.add(
            UserRecord(
                id=user_id,
                email="sqlite@example.com",
                full_name="SQLite User",
                password_hash="hash",
                is_active=True,
                primary_organization_id=organization_id,
                created_at=_now(),
            )
        )
        repository = SqlAlchemyProjectRepository(session)
        project = await repository.create_project(
            organization_id=organization_id,
            user_id=user_id,
            name="SQL Project",
            description=None,
        )
        conversation = await repository.create_conversation(project, user_id, "SQL Conversation")
        message = await repository.create_message(
            conversation,
            user_id,
            message_type=MessageType.USER,
            content="persist me",
        )
        await session.commit()

    async with session_factory() as session:
        repository = SqlAlchemyProjectRepository(session)
        projects, project_total = await repository.list_projects(organization_id, 50, 0)
        conversations, conversation_total = await repository.list_conversations(
            project.id,
            organization_id,
            50,
            0,
        )
        messages, message_total = await repository.list_messages(
            conversation.id,
            organization_id,
            50,
            0,
        )

    assert project_total == 1
    assert projects[0].id == project.id
    assert conversation_total == 1
    assert conversations[0].id == conversation.id
    assert message_total == 1
    assert messages[0].id == message.id
    assert messages[0].content == "persist me"

def _now() -> datetime:
    return datetime.now(UTC)
