from uuid import UUID

from apps.api.app.domain.memory.models import Memory, MemoryCandidate
from apps.api.app.repositories.memory import MemoryRepository

MIN_MEMORY_IMPORTANCE = 0.65


class MemoryService:
    def __init__(self, repository: MemoryRepository) -> None:
        self._repository = repository

    async def store_candidate(
        self,
        organization_id: UUID,
        project_id: UUID,
        user_id: UUID,
        conversation_id: UUID | None,
        candidate: MemoryCandidate,
    ) -> Memory | None:
        if candidate.importance_score < MIN_MEMORY_IMPORTANCE:
            return None
        memory = Memory(
            organization_id=organization_id,
            project_id=project_id,
            user_id=user_id,
            conversation_id=conversation_id,
            memory_class=candidate.memory_class,
            content=candidate.content,
            importance_score=candidate.importance_score,
            source_message_ids=candidate.source_message_ids,
        )
        return await self._repository.create_memory(memory)

    async def search_project_memories(
        self,
        organization_id: UUID,
        project_id: UUID,
        user_id: UUID,
        query: str,
        conversation_id: UUID | None,
        limit: int = 10,
    ) -> list[Memory]:
        return await self._repository.search_project_memories(
            organization_id=organization_id,
            project_id=project_id,
            user_id=user_id,
            query=query,
            limit=limit,
        )

    async def delete_memory(self, organization_id: UUID, user_id: UUID, memory_id: UUID) -> bool:
        return await self._repository.delete_memory(
            organization_id=organization_id,
            user_id=user_id,
            memory_id=memory_id,
        )
