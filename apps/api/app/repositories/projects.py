from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from apps.api.app.db.models.projects import ConversationRecord, MessageRecord, ProjectRecord
from apps.api.app.domain.conversations.models import Conversation, Message, MessageType
from apps.api.app.domain.projects.models import Project


class ProjectRepository(Protocol):
    async def create_project(
        self,
        organization_id: UUID,
        user_id: UUID,
        name: str,
        description: str | None,
    ) -> Project: ...

    async def list_projects(
        self,
        organization_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[Project], int]: ...

    async def get_project(self, project_id: UUID, organization_id: UUID) -> Project | None: ...

    async def update_project(
        self,
        project_id: UUID,
        organization_id: UUID,
        name: str | None,
        description: str | None,
    ) -> Project | None: ...

    async def create_conversation(
        self,
        project: Project,
        user_id: UUID,
        title: str,
    ) -> Conversation: ...

    async def list_conversations(
        self,
        project_id: UUID,
        organization_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[Conversation], int]: ...

    async def get_conversation(
        self,
        conversation_id: UUID,
        organization_id: UUID,
    ) -> Conversation | None: ...

    async def delete_conversation(self, conversation_id: UUID, organization_id: UUID) -> bool: ...

    async def create_message(
        self,
        conversation: Conversation,
        user_id: UUID,
        message_type: MessageType,
        content: str,
    ) -> Message: ...

    async def list_messages(
        self,
        conversation_id: UUID,
        organization_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[Message], int]: ...


def _project_from_record(record: ProjectRecord) -> Project:
    return Project(
        id=record.id,
        organization_id=record.organization_id,
        created_by_user_id=record.created_by_user_id,
        name=record.name,
        description=record.description,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _conversation_from_record(record: ConversationRecord) -> Conversation:
    return Conversation(
        id=record.id,
        project_id=record.project_id,
        organization_id=record.organization_id,
        created_by_user_id=record.created_by_user_id,
        title=record.title,
        is_deleted=record.is_deleted,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _message_from_record(record: MessageRecord) -> Message:
    return Message(
        id=record.id,
        conversation_id=record.conversation_id,
        project_id=record.project_id,
        organization_id=record.organization_id,
        created_by_user_id=record.created_by_user_id,
        message_type=MessageType(record.message_type),
        content=record.content,
        created_at=record.created_at,
    )


class SqlAlchemyProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_project(
        self,
        organization_id: UUID,
        user_id: UUID,
        name: str,
        description: str | None,
    ) -> Project:
        now = datetime.now(UTC)
        record = ProjectRecord(
            id=uuid4(),
            organization_id=organization_id,
            created_by_user_id=user_id,
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
        )
        self._session.add(record)
        await self._session.flush()
        return _project_from_record(record)

    async def list_projects(
        self,
        organization_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[Project], int]:
        total = await self._count(ProjectRecord, ProjectRecord.organization_id == organization_id)
        result = await self._session.execute(
            select(ProjectRecord)
            .where(ProjectRecord.organization_id == organization_id)
            .order_by(ProjectRecord.created_at, ProjectRecord.id)
            .limit(limit)
            .offset(offset)
        )
        return [_project_from_record(record) for record in result.scalars()], total

    async def get_project(self, project_id: UUID, organization_id: UUID) -> Project | None:
        result = await self._session.execute(
            select(ProjectRecord).where(
                ProjectRecord.id == project_id,
                ProjectRecord.organization_id == organization_id,
            )
        )
        record = result.scalar_one_or_none()
        return None if record is None else _project_from_record(record)

    async def update_project(
        self,
        project_id: UUID,
        organization_id: UUID,
        name: str | None,
        description: str | None,
    ) -> Project | None:
        result = await self._session.execute(
            select(ProjectRecord).where(
                ProjectRecord.id == project_id,
                ProjectRecord.organization_id == organization_id,
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            return None
        if name is not None:
            record.name = name
        if description is not None:
            record.description = description
        record.updated_at = datetime.now(UTC)
        await self._session.flush()
        return _project_from_record(record)

    async def create_conversation(
        self,
        project: Project,
        user_id: UUID,
        title: str,
    ) -> Conversation:
        now = datetime.now(UTC)
        record = ConversationRecord(
            id=uuid4(),
            project_id=project.id,
            organization_id=project.organization_id,
            created_by_user_id=user_id,
            title=title,
            is_deleted=False,
            created_at=now,
            updated_at=now,
        )
        self._session.add(record)
        await self._session.flush()
        return _conversation_from_record(record)

    async def list_conversations(
        self,
        project_id: UUID,
        organization_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[Conversation], int]:
        total = await self._count(
            ConversationRecord,
            ConversationRecord.project_id == project_id,
            ConversationRecord.organization_id == organization_id,
            ConversationRecord.is_deleted.is_(False),
        )
        result = await self._session.execute(
            select(ConversationRecord)
            .where(
                ConversationRecord.project_id == project_id,
                ConversationRecord.organization_id == organization_id,
                ConversationRecord.is_deleted.is_(False),
            )
            .order_by(ConversationRecord.created_at, ConversationRecord.id)
            .limit(limit)
            .offset(offset)
        )
        return [_conversation_from_record(record) for record in result.scalars()], total

    async def get_conversation(
        self,
        conversation_id: UUID,
        organization_id: UUID,
    ) -> Conversation | None:
        result = await self._session.execute(
            select(ConversationRecord).where(
                ConversationRecord.id == conversation_id,
                ConversationRecord.organization_id == organization_id,
                ConversationRecord.is_deleted.is_(False),
            )
        )
        record = result.scalar_one_or_none()
        return None if record is None else _conversation_from_record(record)

    async def delete_conversation(self, conversation_id: UUID, organization_id: UUID) -> bool:
        result = await self._session.execute(
            select(ConversationRecord).where(
                ConversationRecord.id == conversation_id,
                ConversationRecord.organization_id == organization_id,
                ConversationRecord.is_deleted.is_(False),
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            return False
        record.is_deleted = True
        record.updated_at = datetime.now(UTC)
        await self._session.flush()
        return True

    async def create_message(
        self,
        conversation: Conversation,
        user_id: UUID,
        message_type: MessageType,
        content: str,
    ) -> Message:
        record = MessageRecord(
            id=uuid4(),
            conversation_id=conversation.id,
            project_id=conversation.project_id,
            organization_id=conversation.organization_id,
            created_by_user_id=user_id,
            message_type=message_type.value,
            content=content,
            created_at=datetime.now(UTC),
        )
        self._session.add(record)
        await self._session.flush()
        return _message_from_record(record)

    async def list_messages(
        self,
        conversation_id: UUID,
        organization_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[Message], int]:
        total = await self._count(
            MessageRecord,
            MessageRecord.conversation_id == conversation_id,
            MessageRecord.organization_id == organization_id,
        )
        result = await self._session.execute(
            select(MessageRecord)
            .where(
                MessageRecord.conversation_id == conversation_id,
                MessageRecord.organization_id == organization_id,
            )
            .order_by(MessageRecord.created_at, MessageRecord.id)
            .limit(limit)
            .offset(offset)
        )
        return [_message_from_record(record) for record in result.scalars()], total

    async def _count(self, model: type[object], *criteria: ColumnElement[bool]) -> int:
        statement = select(func.count()).select_from(model).where(*criteria)
        result = await self._session.execute(statement)
        return int(result.scalar_one())


class InMemoryProjectRepository:
    def __init__(self) -> None:
        self._projects: dict[UUID, Project] = {}
        self._conversations: dict[UUID, Conversation] = {}
        self._messages: dict[UUID, Message] = {}

    async def create_project(
        self,
        organization_id: UUID,
        user_id: UUID,
        name: str,
        description: str | None,
    ) -> Project:
        now = datetime.now(UTC)
        project = Project(
            id=uuid4(),
            organization_id=organization_id,
            created_by_user_id=user_id,
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
        )
        self._projects[project.id] = project
        return project

    async def list_projects(
        self,
        organization_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[Project], int]:
        projects = [
            project
            for project in self._projects.values()
            if project.organization_id == organization_id
        ]
        projects.sort(key=lambda project: (project.created_at, project.id))
        return projects[offset : offset + limit], len(projects)

    async def get_project(self, project_id: UUID, organization_id: UUID) -> Project | None:
        project = self._projects.get(project_id)
        if project is None or project.organization_id != organization_id:
            return None
        return project

    async def update_project(
        self,
        project_id: UUID,
        organization_id: UUID,
        name: str | None,
        description: str | None,
    ) -> Project | None:
        project = await self.get_project(project_id, organization_id)
        if project is None:
            return None
        updated = project.model_copy(
            update={
                "name": name if name is not None else project.name,
                "description": description if description is not None else project.description,
                "updated_at": datetime.now(UTC),
            }
        )
        self._projects[project_id] = updated
        return updated

    async def create_conversation(
        self,
        project: Project,
        user_id: UUID,
        title: str,
    ) -> Conversation:
        now = datetime.now(UTC)
        conversation = Conversation(
            id=uuid4(),
            project_id=project.id,
            organization_id=project.organization_id,
            created_by_user_id=user_id,
            title=title,
            is_deleted=False,
            created_at=now,
            updated_at=now,
        )
        self._conversations[conversation.id] = conversation
        return conversation

    async def list_conversations(
        self,
        project_id: UUID,
        organization_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[Conversation], int]:
        conversations = [
            conversation
            for conversation in self._conversations.values()
            if conversation.project_id == project_id
            and conversation.organization_id == organization_id
            and not conversation.is_deleted
        ]
        conversations.sort(key=lambda conversation: (conversation.created_at, conversation.id))
        return conversations[offset : offset + limit], len(conversations)

    async def get_conversation(
        self,
        conversation_id: UUID,
        organization_id: UUID,
    ) -> Conversation | None:
        conversation = self._conversations.get(conversation_id)
        if (
            conversation is None
            or conversation.organization_id != organization_id
            or conversation.is_deleted
        ):
            return None
        return conversation

    async def delete_conversation(self, conversation_id: UUID, organization_id: UUID) -> bool:
        conversation = await self.get_conversation(conversation_id, organization_id)
        if conversation is None:
            return False
        self._conversations[conversation_id] = conversation.model_copy(
            update={"is_deleted": True, "updated_at": datetime.now(UTC)}
        )
        return True

    async def create_message(
        self,
        conversation: Conversation,
        user_id: UUID,
        message_type: MessageType,
        content: str,
    ) -> Message:
        message = Message(
            id=uuid4(),
            conversation_id=conversation.id,
            project_id=conversation.project_id,
            organization_id=conversation.organization_id,
            created_by_user_id=user_id,
            message_type=message_type,
            content=content,
            created_at=datetime.now(UTC),
        )
        self._messages[message.id] = message
        return message

    async def list_messages(
        self,
        conversation_id: UUID,
        organization_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[Message], int]:
        messages = [
            message
            for message in self._messages.values()
            if message.conversation_id == conversation_id
            and message.organization_id == organization_id
        ]
        messages.sort(key=lambda message: (message.created_at, message.id))
        return messages[offset : offset + limit], len(messages)
