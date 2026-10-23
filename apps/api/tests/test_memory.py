from uuid import UUID, uuid4

import pytest

from apps.api.app.domain.memory.models import (
    Memory,
    MemoryCandidate,
    MemoryClass,
    MemoryStatus,
)
from apps.api.app.repositories.memory import InMemoryMemoryRepository
from apps.api.app.services.memory import MemoryService


@pytest.mark.asyncio
async def test_project_memory_retrieved_across_conversations() -> None:
    repository = InMemoryMemoryRepository()
    service = MemoryService(repository)
    organization_id = uuid4()
    user_id = uuid4()
    project_id = uuid4()
    first_conversation_id = uuid4()
    second_conversation_id = uuid4()

    memory = await service.store_candidate(
        organization_id=organization_id,
        project_id=project_id,
        user_id=user_id,
        conversation_id=first_conversation_id,
        candidate=MemoryCandidate(
            memory_class=MemoryClass.PROJECT_SEMANTIC,
            content="Use ADNI participants with baseline and 12 month visits.",
            importance_score=0.86,
            source_message_ids=[uuid4()],
        ),
    )

    retrieved = await service.search_project_memories(
        organization_id=organization_id,
        project_id=project_id,
        user_id=user_id,
        query="ADNI visit constraints",
        conversation_id=second_conversation_id,
    )

    assert memory is not None
    assert [item.id for item in retrieved] == [memory.id]


@pytest.mark.asyncio
async def test_low_value_chat_is_not_automatically_memorized() -> None:
    repository = InMemoryMemoryRepository()
    service = MemoryService(repository)

    memory = await service.store_candidate(
        organization_id=uuid4(),
        project_id=uuid4(),
        user_id=uuid4(),
        conversation_id=uuid4(),
        candidate=MemoryCandidate(
            memory_class=MemoryClass.CONVERSATION,
            content="ok thanks",
            importance_score=0.2,
            source_message_ids=[uuid4()],
        ),
    )

    assert memory is None
    assert repository.memories == []


@pytest.mark.asyncio
async def test_cross_user_memory_access_is_blocked() -> None:
    repository = InMemoryMemoryRepository()
    service = MemoryService(repository)
    organization_id = uuid4()
    project_id = uuid4()
    owner_id = uuid4()
    other_user_id = uuid4()
    memory = await service.store_candidate(
        organization_id=organization_id,
        project_id=project_id,
        user_id=owner_id,
        conversation_id=uuid4(),
        candidate=stable_preference_candidate(),
    )

    retrieved = await service.search_project_memories(
        organization_id=organization_id,
        project_id=project_id,
        user_id=other_user_id,
        query="preference",
        conversation_id=uuid4(),
    )

    assert memory is not None
    assert retrieved == []


@pytest.mark.asyncio
async def test_memory_deletion_hides_item_from_future_retrieval() -> None:
    repository = InMemoryMemoryRepository()
    service = MemoryService(repository)
    organization_id = uuid4()
    project_id = uuid4()
    user_id = uuid4()
    memory = await service.store_candidate(
        organization_id=organization_id,
        project_id=project_id,
        user_id=user_id,
        conversation_id=uuid4(),
        candidate=stable_preference_candidate(),
    )

    assert memory is not None
    deleted = await service.delete_memory(
        organization_id=organization_id,
        user_id=user_id,
        memory_id=memory.id,
    )
    retrieved = await service.search_project_memories(
        organization_id=organization_id,
        project_id=project_id,
        user_id=user_id,
        query="preference",
        conversation_id=uuid4(),
    )

    assert deleted is True
    assert retrieved == []


def test_memory_model_supports_four_plan_17_memory_classes() -> None:
    assert set(MemoryClass) == {
        MemoryClass.CONVERSATION,
        MemoryClass.PROJECT_SEMANTIC,
        MemoryClass.EPISODIC,
        MemoryClass.DECISION,
    }


def stable_preference_candidate() -> MemoryCandidate:
    return MemoryCandidate(
        memory_class=MemoryClass.DECISION,
        content="Prefer conservative claims unless evidence IDs support stronger wording.",
        importance_score=0.91,
        source_message_ids=[uuid4()],
    )


def memory_fixture(
    organization_id: UUID,
    project_id: UUID,
    user_id: UUID,
    content: str,
) -> Memory:
    return Memory(
        organization_id=organization_id,
        project_id=project_id,
        user_id=user_id,
        conversation_id=uuid4(),
        memory_class=MemoryClass.PROJECT_SEMANTIC,
        content=content,
        importance_score=0.8,
        source_message_ids=[uuid4()],
        status=MemoryStatus.ACTIVE,
    )
