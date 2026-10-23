from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.db.models.memory import MemoryRecord
from apps.api.app.domain.memory.models import Memory, MemoryClass, MemoryStatus


class MemoryRepository(Protocol):
    async def create_memory(self, memory: Memory) -> Memory: ...

    async def search_project_memories(
        self,
        organization_id: UUID,
        project_id: UUID,
        user_id: UUID,
        query: str,
        limit: int,
    ) -> list[Memory]: ...

    async def delete_memory(
        self,
        organization_id: UUID,
        user_id: UUID,
        memory_id: UUID,
    ) -> bool: ...


class SqlAlchemyMemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_memory(self, memory: Memory) -> Memory:
        self._session.add(
            MemoryRecord(
                id=memory.id,
                organization_id=memory.organization_id,
                project_id=memory.project_id,
                user_id=memory.user_id,
                conversation_id=memory.conversation_id,
                memory_class=memory.memory_class.value,
                content=memory.content,
                importance_score=memory.importance_score,
                source_message_ids=[str(message_id) for message_id in memory.source_message_ids],
                status=memory.status.value,
                created_at=memory.created_at,
                updated_at=memory.updated_at,
            )
        )
        await self._session.flush()
        return memory

    async def search_project_memories(
        self,
        organization_id: UUID,
        project_id: UUID,
        user_id: UUID,
        query: str,
        limit: int,
    ) -> list[Memory]:
        query_terms = _query_terms(query)
        result = await self._session.execute(
            select(MemoryRecord).where(
                MemoryRecord.organization_id == organization_id,
                MemoryRecord.project_id == project_id,
                MemoryRecord.user_id == user_id,
                MemoryRecord.status == MemoryStatus.ACTIVE.value,
            )
        )
        memories = [_memory_from_record(record) for record in result.scalars()]
        return _rank_memories(memories, query_terms)[:limit]

    async def delete_memory(self, organization_id: UUID, user_id: UUID, memory_id: UUID) -> bool:
        result = await self._session.execute(
            select(MemoryRecord).where(
                MemoryRecord.id == memory_id,
                MemoryRecord.organization_id == organization_id,
                MemoryRecord.user_id == user_id,
                MemoryRecord.status == MemoryStatus.ACTIVE.value,
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            return False
        record.status = MemoryStatus.DELETED.value
        record.updated_at = datetime.now(UTC)
        await self._session.flush()
        return True


class InMemoryMemoryRepository:
    def __init__(self) -> None:
        self.memories: list[Memory] = []

    async def create_memory(self, memory: Memory) -> Memory:
        self.memories.append(memory)
        return memory

    async def search_project_memories(
        self,
        organization_id: UUID,
        project_id: UUID,
        user_id: UUID,
        query: str,
        limit: int,
    ) -> list[Memory]:
        query_terms = _query_terms(query)
        scoped = [
            memory
            for memory in self.memories
            if memory.organization_id == organization_id
            and memory.project_id == project_id
            and memory.user_id == user_id
            and memory.status == MemoryStatus.ACTIVE
        ]
        return _rank_memories(scoped, query_terms)[:limit]

    async def delete_memory(self, organization_id: UUID, user_id: UUID, memory_id: UUID) -> bool:
        for index, memory in enumerate(self.memories):
            if (
                memory.id == memory_id
                and memory.organization_id == organization_id
                and memory.user_id == user_id
                and memory.status == MemoryStatus.ACTIVE
            ):
                self.memories[index] = memory.model_copy(
                    update={
                        "status": MemoryStatus.DELETED,
                        "updated_at": datetime.now(UTC),
                    }
                )
                return True
        return False


def _memory_from_record(record: MemoryRecord) -> Memory:
    return Memory(
        id=record.id,
        organization_id=record.organization_id,
        project_id=record.project_id,
        user_id=record.user_id,
        conversation_id=record.conversation_id,
        memory_class=MemoryClass(record.memory_class),
        content=record.content,
        importance_score=record.importance_score,
        source_message_ids=[UUID(message_id) for message_id in record.source_message_ids],
        status=MemoryStatus(record.status),
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _rank_memories(memories: list[Memory], query_terms: set[str]) -> list[Memory]:
    return sorted(
        memories,
        key=lambda memory: (_score_memory(memory, query_terms), memory.created_at),
        reverse=True,
    )


def _score_memory(memory: Memory, query_terms: set[str]) -> float:
    if not query_terms:
        return memory.importance_score
    content_terms = set(memory.content.lower().split())
    overlap = len(query_terms.intersection(content_terms))
    return memory.importance_score + overlap


def _query_terms(query: str) -> set[str]:
    return {term.strip(".,;:!?()[]").lower() for term in query.split() if term.strip()}
