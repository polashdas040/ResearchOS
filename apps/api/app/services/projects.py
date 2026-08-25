from uuid import UUID

from apps.api.app.domain.conversations.models import Conversation, Message, MessageType
from apps.api.app.domain.projects.models import Project
from apps.api.app.domain.users.models import User
from apps.api.app.repositories.projects import ProjectRepository


class ResourceNotFoundError(Exception):
    """Raised when a tenant-scoped resource is missing or inaccessible."""


class ProjectService:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    async def create_project(
        self,
        user: User,
        name: str,
        description: str | None,
    ) -> Project:
        return await self._repository.create_project(
            organization_id=user.primary_organization_id,
            user_id=user.id,
            name=name,
            description=description,
        )

    async def list_projects(self, user: User, limit: int, offset: int) -> tuple[list[Project], int]:
        return await self._repository.list_projects(
            organization_id=user.primary_organization_id,
            limit=limit,
            offset=offset,
        )

    async def get_project(self, user: User, project_id: UUID) -> Project:
        project = await self._repository.get_project(project_id, user.primary_organization_id)
        if project is None:
            raise ResourceNotFoundError("Project not found")
        return project

    async def update_project(
        self,
        user: User,
        project_id: UUID,
        name: str | None,
        description: str | None,
    ) -> Project:
        project = await self._repository.update_project(
            project_id=project_id,
            organization_id=user.primary_organization_id,
            name=name,
            description=description,
        )
        if project is None:
            raise ResourceNotFoundError("Project not found")
        return project

    async def create_conversation(self, user: User, project_id: UUID, title: str) -> Conversation:
        project = await self.get_project(user, project_id)
        return await self._repository.create_conversation(
            project=project,
            user_id=user.id,
            title=title,
        )

    async def list_conversations(
        self,
        user: User,
        project_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[Conversation], int]:
        await self.get_project(user, project_id)
        return await self._repository.list_conversations(
            project_id=project_id,
            organization_id=user.primary_organization_id,
            limit=limit,
            offset=offset,
        )

    async def get_conversation(self, user: User, conversation_id: UUID) -> Conversation:
        conversation = await self._repository.get_conversation(
            conversation_id=conversation_id,
            organization_id=user.primary_organization_id,
        )
        if conversation is None:
            raise ResourceNotFoundError("Conversation not found")
        return conversation

    async def delete_conversation(self, user: User, conversation_id: UUID) -> None:
        deleted = await self._repository.delete_conversation(
            conversation_id=conversation_id,
            organization_id=user.primary_organization_id,
        )
        if not deleted:
            raise ResourceNotFoundError("Conversation not found")

    async def create_message(
        self,
        user: User,
        conversation_id: UUID,
        message_type: MessageType,
        content: str,
    ) -> Message:
        conversation = await self.get_conversation(user, conversation_id)
        return await self._repository.create_message(
            conversation=conversation,
            user_id=user.id,
            message_type=message_type,
            content=content,
        )

    async def get_conversation_with_messages(
        self,
        user: User,
        conversation_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[Conversation, list[Message], int]:
        conversation = await self.get_conversation(user, conversation_id)
        messages, total = await self._repository.list_messages(
            conversation_id=conversation.id,
            organization_id=user.primary_organization_id,
            limit=limit,
            offset=offset,
        )
        return conversation, messages, total
